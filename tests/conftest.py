from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

import pytest

from drivers.appium_driver import AppiumDriverFactory
from drivers.device_manager import DeviceManager
from drivers.playwright_driver import PlaywrightDriverFactory
from utils.config_loader import (
    load_capabilities_doc,
    load_devices,
    merged_appium_capabilities,
    project_root,
)
from utils.order_data import load_order_profile


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--channel",
        action="store",
        default=os.getenv("TEST_CHANNEL", "web"),
        choices=("web", "api", "tablet"),
        help=(
            "web=Playwright POS; api=HTTP submit; tablet=skip web/API, only validate KDS "
            "(assume order already on tablets or you only check UI)."
        ),
    )
    parser.addoption(
        "--order",
        action="store",
        default=os.getenv("TEST_ORDER_PROFILE", "sample_order"),
        help="Key from data/orders.json to load as the order payload.",
    )
    parser.addoption(
        "--skip-preflight",
        action="store_true",
        default=False,
        help="Skip Appium device/app availability precheck for integration/e2e tests.",
    )
    parser.addoption(
        "--preflight-roles",
        action="store",
        default="",
        help="Comma-separated logical roles to precheck (default: all roles from config/devices.yaml).",
    )
    parser.addoption(
        "--record-device-video",
        action="store_true",
        default=False,
        help="Record Android device screen per test and save MP4 files to reports/videos.",
    )
    parser.addoption(
        "--video-role",
        action="store",
        default="pilot",
        help="Logical role from config/devices.yaml to record when --record-device-video is enabled.",
    )
    parser.addoption(
        "--persist-healed-udid",
        action="store_true",
        default=False,
        help=(
            "When wireless ADB port drifts, write the resolved udid to config/local.yaml "
            "(HEAL_WIRELESS_UDID_PERSIST)."
        ),
    )
    parser.addoption(
        "--no-wireless-udid-heal",
        action="store_true",
        default=False,
        help="Disable automatic IPv4:port udid remap when the tablet reconnects on a new port.",
    )


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--persist-healed-udid"):
        os.environ["HEAL_WIRELESS_UDID_PERSIST"] = "1"
    if config.getoption("--no-wireless-udid-heal"):
        os.environ["HEAL_WIRELESS_UDID"] = "0"


_PREFLIGHT_RAN = False


def pytest_runtest_setup(item: pytest.Item) -> None:
    global _PREFLIGHT_RAN
    if _PREFLIGHT_RAN:
        return
    if item.config.getoption("--skip-preflight"):
        return
    if not (item.get_closest_marker("integration") or item.get_closest_marker("e2e")):
        return
    _run_preflight_or_fail(item.config)
    _PREFLIGHT_RAN = True


def _run_preflight_or_fail(config: pytest.Config) -> None:
    devices_doc = load_devices().get("devices") or {}
    caps_doc = load_capabilities_doc().get("apps") or {}

    roles_csv = str(config.getoption("--preflight-roles") or "").strip()
    if roles_csv:
        roles = [r.strip() for r in roles_csv.split(",") if r.strip()]
    else:
        roles = list(devices_doc.keys())

    if not roles:
        pytest.fail("Preflight failed: no roles found in config/devices.yaml", pytrace=False)

    factory = AppiumDriverFactory()
    errors: list[str] = []
    for role in roles:
        if role not in devices_doc:
            errors.append(f"{role}: missing in config/devices.yaml")
            continue
        if role not in caps_doc:
            errors.append(f"{role}: missing in config/capabilities.yaml apps block")
            continue

        driver = None
        try:
            caps = merged_appium_capabilities(role)
            driver = factory.create_driver(role)
            app_pkg = caps.get("appium:appPackage") or caps.get("appPackage")
            if app_pkg and not driver.is_app_installed(str(app_pkg)):
                errors.append(f"{role}: app package not installed/reachable: {app_pkg}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{role}: unable to create Appium session ({exc})")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    if errors:
        msg = "Preflight failed (device/app availability):\n- " + "\n- ".join(errors)
        pytest.fail(msg, pytrace=False)


@pytest.fixture(autouse=True)
def record_device_video(request: pytest.FixtureRequest):
    """
    Optional per-test device recording.

    Enable with:
      pytest --record-device-video --video-role pilot
    """
    if not request.config.getoption("--record-device-video"):
        yield
        return

    # Limit recording to mobile/integration style tests to avoid noise.
    node = request.node
    if not (
        node.get_closest_marker("integration")
        or node.get_closest_marker("e2e")
        or node.get_closest_marker("functional")
    ):
        yield
        return

    role = str(request.config.getoption("--video-role") or "pilot").strip()
    devices = (load_devices().get("devices") or {})
    device_entry = devices.get(role) or {}
    udid = str(device_entry.get("udid") or "").strip()
    if not udid or udid.startswith("REPLACE_"):
        print(f"[video] skip: invalid/missing udid for role '{role}'")
        yield
        return

    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", node.nodeid)
    stamp = int(time.time())
    remote_mp4 = f"/sdcard/{role}_{stamp}.mp4"
    out_dir: Path = project_root() / "reports" / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    local_mp4 = out_dir / f"{safe_name}_{stamp}.mp4"

    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            ["adb", "-s", udid, "shell", "screenrecord", "--bit-rate", "8000000", remote_mp4],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        # Give screenrecord a moment to start.
        time.sleep(1.0)
    except Exception as exc:  # noqa: BLE001
        print(f"[video] failed to start recording for {role} ({udid}): {exc}")

    try:
        yield
    finally:
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        # Pull and cleanup remote file (best-effort).
        try:
            subprocess.run(
                ["adb", "-s", udid, "pull", remote_mp4, str(local_mp4)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            subprocess.run(
                ["adb", "-s", udid, "shell", "rm", "-f", remote_mp4],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if local_mp4.exists():
                print(f"[video] saved: {local_mp4}")
        except Exception as exc:  # noqa: BLE001
            print(f"[video] failed to pull recording from {udid}: {exc}")


@pytest.fixture
def channel(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--channel")


@pytest.fixture
def order_profile(request: pytest.FixtureRequest) -> dict:
    key = request.config.getoption("--order")
    return load_order_profile(key)


@pytest.fixture
def device_manager() -> DeviceManager:
    manager = DeviceManager()
    yield manager
    manager.quit_all()


@pytest.fixture
def playwright_factory() -> PlaywrightDriverFactory:
    factory = PlaywrightDriverFactory()
    yield factory
    factory.stop()


@pytest.fixture
def pos_browser_page(request: pytest.FixtureRequest, playwright_factory: PlaywrightDriverFactory):
    if request.config.getoption("--channel") != "web":
        yield None
        return
    browser = playwright_factory.start(headless=True)
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
