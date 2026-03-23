from __future__ import annotations

import os

import pytest

from drivers.appium_driver import AppiumDriverFactory
from drivers.device_manager import DeviceManager
from drivers.playwright_driver import PlaywrightDriverFactory
from utils.config_loader import load_capabilities_doc, load_devices, merged_appium_capabilities
from utils.order_data import load_order_profile


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--channel",
        action="store",
        default=os.getenv("TEST_CHANNEL", "web"),
        choices=("web", "api"),
        help="How the order is submitted: web (Playwright POS) or api (HTTP).",
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


_PREFLIGHT_RAN = False


def pytest_runtest_setup(item: pytest.Item) -> None:
    global _PREFLIGHT_RAN
    if _PREFLIGHT_RAN:
        return
    if item.config.getoption("--skip-preflight"):
        return
    if os.getenv("RUN_E2E") != "1":
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
