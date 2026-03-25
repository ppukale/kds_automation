from __future__ import annotations

import pytest

from pages.mobile.pilot_page import PilotPage


@pytest.mark.functional
@pytest.mark.integration
def test_pilot_station_elements_and_drop_sides(device_manager) -> None:
    """Pilot station app: verify required elements and tap Drop Sides."""
    page = PilotPage(device_manager.get("pilot"))
    page.run_station_smoke_checks(customer_name="sravani kompall", tap_drop_sides=True)
