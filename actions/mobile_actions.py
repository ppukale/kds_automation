from __future__ import annotations

from typing import Any

from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class MobileActions:
    """Generic mobile gestures and waits (use inside page objects)."""

    def __init__(self, driver: WebDriver, default_timeout_s: float = 20.0) -> None:
        self.driver = driver
        self.default_timeout_s = default_timeout_s

    def wait_visible(self, locator: tuple[str, str], timeout_s: float | None = None) -> Any:
        wait = WebDriverWait(self.driver, timeout_s or self.default_timeout_s)
        return wait.until(ec.visibility_of_element_located(locator))

    def tap(self, locator: tuple[str, str], timeout_s: float | None = None) -> None:
        el = self.wait_visible(locator, timeout_s)
        el.click()

    def tap_clickable(self, locator: tuple[str, str], timeout_s: float | None = None) -> None:
        """Use when visibility_of_element_located fails but the control is still clickable (common on Android)."""
        wait = WebDriverWait(self.driver, timeout_s or self.default_timeout_s)
        el = wait.until(ec.element_to_be_clickable(locator))
        el.click()

    def type_text(self, locator: tuple[str, str], text: str, *, timeout_s: float | None = None) -> None:
        el = self.wait_visible(locator, timeout_s)
        el.clear()
        el.send_keys(text)
