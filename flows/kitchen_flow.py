from __future__ import annotations

from drivers.device_manager import DeviceManager
from pages.mobile.bombardier_page import BombardierPage
from pages.mobile.wingman_page import WingmanPage


class KitchenFlow:
    """Tablet-side kitchen / KDS style interactions across roles."""

    def __init__(self, devices: DeviceManager) -> None:
        self._devices = devices

    def kitchen_surfaces_ready(self) -> dict[str, bool]:
        return {
            "bombardier": BombardierPage(self._devices.get("bombardier")).is_displayed(),
            "wingman": WingmanPage(self._devices.get("wingman")).is_displayed(),
        }
