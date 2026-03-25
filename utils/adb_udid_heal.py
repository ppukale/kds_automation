from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

_IPV4_PORT = re.compile(r"^(?P<host>\d{1,3}(?:\.\d{1,3}){3}):(?P<port>\d+)$")
_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _list_adb_devices() -> list[tuple[str, str]]:
    try:
        proc = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    rows: list[tuple[str, str]] = []
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("list of devices"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            rows.append((parts[0], parts[-1]))
    return rows


def maybe_heal_wireless_udid(configured: str, *, role: str = "") -> str:
    """
    If UDID looks like IPv4:port and that serial is missing from ADB, use the
    same IP with whatever port ADB currently reports (wireless debug port drift).
    """
    configured = str(configured).strip()
    m = _IPV4_PORT.match(configured)
    if not m:
        return configured

    host = m.group("host")
    rows = _list_adb_devices()
    online = {serial for serial, state in rows if state == "device"}

    if configured in online:
        return configured

    prefix = host + ":"
    candidates = sorted(s for s in online if s.startswith(prefix))
    if len(candidates) == 1:
        new_udid = candidates[0]
        label = f"[{role}] " if role else ""
        print(f"[udid-heal] {label}{configured} -> {new_udid} (wireless ADB port changed)")
        return new_udid
    if len(candidates) > 1:
        print(
            f"[udid-heal] multiple online devices for {host}: {candidates}; "
            f"not auto-switching from {configured}"
        )
    return configured


def persist_healed_udid_local(role: str, udid: str) -> None:
    """Write UDID under devices.<role> in config/local.yaml (gitignored)."""
    path = _CONFIG_DIR / "local.yaml"
    data: dict[str, Any]
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        data = loaded if isinstance(loaded, dict) else {}
    else:
        data = {}

    devices = dict(data.get("devices") or {})
    role_entry = dict(devices.get(role) or {})
    role_entry["udid"] = udid
    devices[role] = role_entry
    data["devices"] = devices

    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
