from __future__ import annotations

import time
from typing import Any

from drivers.device_manager import DeviceManager
from pages.mobile.bombardier_page import BombardierPage
from pages.mobile.gunner_page import GunnerPage
from pages.mobile.pilot_page import PilotPage
from pages.mobile.wingman_page import WingmanPage
from utils.config_loader import load_env
from utils.kitchen_expectations import (
    line_display_strings_for_items,
    order_number_from_order,
    partition_order_for_stations,
)


class KitchenStationValidation:
    """After Web/API submission, assert order id, quantities, and line routing on KDS tablets."""

    def __init__(self, devices: DeviceManager) -> None:
        self._devices = devices

    def validate_order_on_tablets(self, order: dict[str, Any]) -> None:
        items = order.get("items") or []
        if not items:
            return

        env = load_env()
        kcfg = env.get("kitchen") or {}
        wait_s = float(kcfg.get("sync_wait_s") or 0)
        verify_ticket = bool(kcfg.get("verify_order_number", True))
        if wait_s > 0:
            time.sleep(wait_s)

        part = partition_order_for_stations(order)
        ticket = order_number_from_order(order) if verify_ticket else None

        def assert_station(
            station_name: str,
            page: GunnerPage | BombardierPage | WingmanPage | PilotPage,
            rows: list[dict[str, Any]],
        ) -> None:
            try:
                if ticket:
                    page.assert_line_texts_visible([ticket])
                lines = line_display_strings_for_items(rows)
                if lines:
                    page.assert_line_texts_visible(lines)
            except AssertionError as exc:
                raise AssertionError(f"{station_name} validation failed: {exc}") from exc

        # POC sequence: Pilot first, then downstream stations.
        assert_station("pilot", PilotPage(self._devices.get("pilot")), items)

        # Then validate routed stations only when items are present for that station.
        if part["gunner"]:
            assert_station("gunner", GunnerPage(self._devices.get("gunner")), part["gunner"])
        if part["bombardier"]:
            assert_station("bombardier", BombardierPage(self._devices.get("bombardier")), part["bombardier"])
        if part["wingman"]:
            assert_station("wingman", WingmanPage(self._devices.get("wingman")), part["wingman"])
