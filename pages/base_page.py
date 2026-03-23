from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver

from actions.mobile_actions import MobileActions


class BaseMobilePage:
    """Shared mobile page object base."""

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        self.actions = MobileActions(driver)

    def assert_line_texts_visible(self, texts: list[str], *, timeout_s: float = 25.0) -> None:
        """Assert each string appears in the visible hierarchy (tune XPath per app if needed)."""
        missing: list[str] = []
        for text in texts:
            if not text:
                continue
            safe = text.replace('"', '\\"')
            loc = (AppiumBy.XPATH, f'//*[contains(@text, "{safe}")]')
            try:
                self.actions.wait_visible(loc, timeout_s=timeout_s)
            except Exception:
                missing.append(text)
        if missing:
            raise AssertionError(
                f"Expected text not visible on {self.__class__.__name__}: {missing}"
            )
