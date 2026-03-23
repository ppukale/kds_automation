from __future__ import annotations

from drivers.device_manager import DeviceManager
from pages.mobile.expo_page import ExpoPage
from pages.mobile.pilot_page import PilotPage


class ValidationFlow:
    """Cross-device checks — extend with API + UI correlation."""

    def __init__(self, devices: DeviceManager) -> None:
        self._devices = devices

    def pilot_and_expo_visible(self) -> dict[str, bool]:
        return {
            "pilot": PilotPage(self._devices.get("pilot")).is_displayed(),
            "expo": ExpoPage(self._devices.get("expo")).is_displayed(),
        }
