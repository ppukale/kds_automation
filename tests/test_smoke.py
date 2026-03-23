from __future__ import annotations

import pytest

from utils import config_loader


@pytest.mark.smoke
def test_config_files_load() -> None:
    devices = config_loader.load_devices()
    assert "devices" in devices
    for role in ("gunner", "bombardier", "wingman", "pilot", "expo"):
        assert role in devices["devices"]

    env = config_loader.load_env()
    assert "environment" in env

    caps = config_loader.load_capabilities_doc()
    assert "common" in caps
    assert "apps" in caps
    assert "emulator_common" in caps


@pytest.mark.smoke
def test_line_display_includes_quantity() -> None:
    from utils.kitchen_expectations import line_display_text_for_assertion

    line = line_display_text_for_assertion(
        {"sku": "X", "display_name": "Large Fries", "qty": 3}
    )
    assert "3" in line and "Large Fries" in line


@pytest.mark.smoke
def test_kitchen_partition_matches_tags() -> None:
    from utils.kitchen_expectations import partition_order_for_stations
    from utils.order_data import load_order_profile

    order = load_order_profile("multi_station_order")
    part = partition_order_for_stations(order)
    assert len(part["gunner"]) >= 1
    assert len(part["bombardier"]) >= 1
    assert len(part["wingman"]) >= 1
    assert len(part["pilot"]) == len(order["items"])


@pytest.mark.smoke
def test_load_order_profile_from_orders_json() -> None:
    from utils.order_data import load_order_profile

    profile = load_order_profile("sample_order")
    assert "items" in profile


@pytest.mark.smoke
def test_merged_capabilities_requires_real_udid() -> None:
    with pytest.raises(ValueError, match="Set a real UDID"):
        config_loader.merged_appium_capabilities("gunner")
