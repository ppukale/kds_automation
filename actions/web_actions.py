from __future__ import annotations

from playwright.sync_api import Locator, Page


class WebActions:
    """Thin helpers around Playwright for shared web patterns."""

    def __init__(self, page: Page, default_timeout_ms: int = 30_000) -> None:
        self.page = page
        self.default_timeout_ms = default_timeout_ms

    def click(self, locator: Locator) -> None:
        locator.click(timeout=self.default_timeout_ms)

    def fill(self, locator: Locator, text: str) -> None:
        locator.fill(text, timeout=self.default_timeout_ms)
