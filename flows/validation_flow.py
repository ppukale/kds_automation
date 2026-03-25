from __future__ import annotations

from drivers.device_manager import DeviceManager
from pages.mobile.pilot_page import PilotPage


class ValidationFlow:
    """Cross-device checks — extend with API + UI correlation."""

    def __init__(self, devices: DeviceManager) -> None:
        self._devices = devices

    def pilot_visible(self) -> bool:
        return PilotPage(self._devices.get("pilot")).is_displayed()
