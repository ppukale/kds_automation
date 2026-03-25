from __future__ import annotations

import pytest

from flows.kitchen_station_validation import KitchenStationValidation
from flows.order_flow import OrderFlow
from utils.web_env import configured_web_base_url, web_base_url_skip_reason


@pytest.mark.e2e
@pytest.mark.integration
def test_order_end_to_end(
    device_manager,
    pos_browser_page,
    channel: str,
    order_profile: dict,
) -> None:
    if channel == "web" and configured_web_base_url() is None:
        pytest.skip(web_base_url_skip_reason())

    flow = OrderFlow(
        device_manager,
        channel=channel,
        order=order_profile,
        pos_page=pos_browser_page,
    )
    flow.place_order()
    KitchenStationValidation(device_manager).validate_order_on_tablets(order_profile)
