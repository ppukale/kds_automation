from __future__ import annotations

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BaseMobilePage


class PilotPage(BaseMobilePage):
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
