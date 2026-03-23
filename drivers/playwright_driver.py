from __future__ import annotations

from playwright.sync_api import Browser, Playwright, sync_playwright

from utils.config_loader import load_env


class PlaywrightDriverFactory:
    """Starts Playwright and returns a configured browser instance."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def start(self, *, headless: bool = False) -> Browser:
        env = load_env()
        web_cfg = env.get("web") or {}
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        return self._browser

    def stop(self) -> None:
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
