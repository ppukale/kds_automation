from __future__ import annotations

import os

import pytest

from flows.kitchen_station_validation import KitchenStationValidation
from flows.order_flow import OrderFlow


@pytest.mark.e2e
@pytest.mark.integration
def test_order_end_to_end(
    device_manager,
    pos_browser_page,
    channel: str,
    order_profile: dict,
) -> None:
    if os.getenv("RUN_E2E") != "1":
        pytest.skip("Set RUN_E2E=1, configure UDIDs, Appium, apps, and POS URL.")

    flow = OrderFlow(
        device_manager,
        channel=channel,
        order=order_profile,
        pos_page=pos_browser_page,
    )
    flow.place_order()
    KitchenStationValidation(device_manager).validate_order_on_tablets(order_profile)
