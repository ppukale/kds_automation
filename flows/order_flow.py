from __future__ import annotations

from typing import Any

from playwright.sync_api import Page

from drivers.device_manager import DeviceManager
from pages.mobile.gunner_page import GunnerPage
from pages.web.pos_page import PosPage
from services.order_api import submit_order_via_api


class OrderFlow:
    """Place orders via Web (POS) or API; assert on kitchen tablets."""

    def __init__(
        self,
        devices: DeviceManager,
        channel: str,
        order: dict[str, Any],
        pos_page: Page | None = None,
    ) -> None:
        self._devices = devices
        self._channel = channel.lower().strip()
        self._order = order
        self._pos_page = pos_page
        self._pos: PosPage | None = PosPage(pos_page) if pos_page is not None else None

    def place_order(self) -> None:
        if self._channel == "web":
            if self._pos is None:
                raise RuntimeError("Web channel requires a Playwright Page (browser session).")
            self._pos.place_order_from_data(self._order)
        elif self._channel == "api":
            submit_order_via_api(self._order)
        elif self._channel == "tablet":
            # No Playwright; no API submit — only KDS assertions (order must exist via other means).
            return
        else:
            raise ValueError(
                f"Unsupported channel: {self._channel!r}. Use 'web', 'api', or 'tablet'."
            )

    def gunner_sees_app_shell(self) -> bool:
        driver = self._devices.get("gunner")
        return GunnerPage(driver).is_displayed()
