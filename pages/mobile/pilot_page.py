from __future__ import annotations

import re

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BaseMobilePage


class PilotPage(BaseMobilePage):
    # Timer like 00:38 (value changes, format should remain mm:ss).
    TIMER_TEXT_ANY_MMSS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[string-length(@text)=5 and substring(@text,3,1)=":"]',
    )
    ORDER_NUMBER_BLOCK = (
        AppiumBy.XPATH,
        '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/'
        "android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.ScrollView/"
        "android.view.ViewGroup/android.view.ViewGroup/android.widget.HorizontalScrollView/"
        "android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]",
    )
    ORDER_TYPE_BLOCK = (
        AppiumBy.XPATH,
        '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/'
        "android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.ScrollView/"
        "android.view.ViewGroup/android.view.ViewGroup/android.widget.HorizontalScrollView/"
        "android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup",
    )
    WINGS_IMAGE = (
        AppiumBy.XPATH,
        '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/'
        "android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.ScrollView/"
        "android.view.ViewGroup/android.view.ViewGroup/android.widget.HorizontalScrollView/android.view.ViewGroup/"
        "android.view.ViewGroup/android.view.ViewGroup/android.widget.HorizontalScrollView[2]/android.view.ViewGroup/"
        "android.widget.ScrollView/android.view.ViewGroup/android.widget.ScrollView[3]/android.view.ViewGroup/"
        "android.view.ViewGroup/android.widget.ImageView",
    )
    DROP_SIDES_BUTTON = (
        AppiumBy.XPATH,
        '//android.view.ViewGroup[@content-desc="Drop Sides"]/android.widget.ImageView',
    )

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)

    def root(self):
        return (AppiumBy.ACCESSIBILITY_ID, "pilot_root")

    def is_displayed(self) -> bool:
        try:
            self.actions.wait_visible(self.root(), timeout_s=5)
            return True
        except Exception:
            return False

    def assert_timer_bar_displayed(self, *, timeout_s: float = 20.0) -> None:
        el = self.actions.wait_visible(self.TIMER_TEXT_ANY_MMSS, timeout_s=timeout_s)
        timer_text = str(el.get_attribute("text") or "").strip()
        if not re.fullmatch(r"\d{2}:\d{2}", timer_text):
            raise AssertionError(f"Expected timer in mm:ss format, got: {timer_text!r}")

    def assert_order_number_block_displayed(self, *, timeout_s: float = 20.0) -> None:
        self.actions.wait_visible(self.ORDER_NUMBER_BLOCK, timeout_s=timeout_s)

    def assert_order_type_block_displayed(self, *, timeout_s: float = 20.0) -> None:
        self.actions.wait_visible(self.ORDER_TYPE_BLOCK, timeout_s=timeout_s)

    def assert_customer_name_displayed(self, customer_name: str, *, timeout_s: float = 20.0) -> None:
        name_loc = (AppiumBy.XPATH, f'//android.widget.TextView[@text="{customer_name}"]')
        self.actions.wait_visible(name_loc, timeout_s=timeout_s)

    def assert_wings_displayed(self, *, timeout_s: float = 20.0) -> None:
        self.actions.wait_visible(self.WINGS_IMAGE, timeout_s=timeout_s)

    def tap_drop_sides(self, *, timeout_s: float = 20.0) -> None:
        self.actions.tap(self.DROP_SIDES_BUTTON, timeout_s=timeout_s)

    def run_station_smoke_checks(
        self,
        *,
        customer_name: str = "sravani kompall",
        tap_drop_sides: bool = True,
        timeout_s: float = 20.0,
    ) -> None:
        """
        Beginner-friendly one-call check for the Pilot station screen.
        Keep tests short and pass only values that change per scenario.
        """
        self.assert_timer_bar_displayed(timeout_s=timeout_s)
        self.assert_order_number_block_displayed(timeout_s=timeout_s)
        self.assert_order_type_block_displayed(timeout_s=timeout_s)
        self.assert_customer_name_displayed(customer_name, timeout_s=timeout_s)
        self.assert_wings_displayed(timeout_s=timeout_s)
        if tap_drop_sides:
            self.tap_drop_sides(timeout_s=timeout_s)
