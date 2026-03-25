from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from utils.adb_udid_heal import maybe_heal_wireless_udid, persist_healed_udid_local

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _PROJECT_ROOT / "config"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at root of {path}")
    return data


def project_root() -> Path:
    return _PROJECT_ROOT


def load_devices() -> dict[str, Any]:
    base = _read_yaml(_CONFIG_DIR / "devices.yaml")
    local = _read_yaml(_CONFIG_DIR / "local.yaml")
    out: dict[str, Any] = dict(base)
    devices_base: dict[str, Any] = dict(out.get("devices") or {})
    raw_local_dev = local.get("devices")
    local_dev = raw_local_dev if isinstance(raw_local_dev, dict) else {}
    if local_dev:
        devices_base = _deep_merge(devices_base, local_dev)
    out["devices"] = devices_base
    return out


def load_env() -> dict[str, Any]:
    merged = _read_yaml(_CONFIG_DIR / "env.yaml")
    local = _read_yaml(_CONFIG_DIR / "local.yaml")
    if local:
        merged = _deep_merge(merged, local)
    return merged


def load_capabilities_doc() -> dict[str, Any]:
    return _read_yaml(_CONFIG_DIR / "capabilities.yaml")


def merged_appium_capabilities(role: str) -> dict[str, Any]:
    """Merge common caps + per-app caps + device udid for a logical role."""
    doc = load_capabilities_doc()
    common = doc.get("common") or {}
    apps = doc.get("apps") or {}
    devices_doc = load_devices()
    devices = devices_doc.get("devices") or {}

    if role not in apps:
        raise KeyError(f"Unknown app role in capabilities.yaml: {role}")
    if role not in devices:
        raise KeyError(f"Unknown device role in devices.yaml: {role}")

    per_app = apps[role] or {}
    device_entry = devices[role] or {}
    udid = device_entry.get("udid")
    if not udid or str(udid).startswith("REPLACE_"):
        raise ValueError(
            f"Set a real UDID in config/devices.yaml for role '{role}' "
            f"(current: {udid!r})"
        )

    caps: dict[str, Any] = {}
    caps.update(common)
    kind = str(device_entry.get("kind") or "").lower()
    if kind == "emulator":
        emulator_common = doc.get("emulator_common") or {}
        caps.update(emulator_common)
    elif kind == "device":
        device_common = doc.get("device_common") or {}
        caps.update(device_common)
    caps.update(per_app)
    udid_str = str(udid).strip()
    heal_on = os.getenv("HEAL_WIRELESS_UDID", "1").lower() in ("1", "true", "yes")
    if heal_on:
        healed = maybe_heal_wireless_udid(udid_str, role=role)
        persist_on = os.getenv("HEAL_WIRELESS_UDID_PERSIST", "").lower() in (
            "1",
            "true",
            "yes",
        )
        if persist_on and healed != udid_str:
            persist_healed_udid_local(role, healed)
        udid_str = healed
    caps["udid"] = udid_str
    return caps


def _deep_merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out
