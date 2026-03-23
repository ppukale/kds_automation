from __future__ import annotations

from typing import Any

from appium import webdriver
from appium.options.android import UiAutomator2Options

from utils.config_loader import load_env, merged_appium_capabilities


class AppiumDriverFactory:
    """Builds Android UiAutomator2 sessions from YAML config."""

    def __init__(self, server_url: str | None = None) -> None:
        env = load_env()
        appium_cfg = env.get("appium") or {}
        self._server_url = server_url or appium_cfg.get("server_url") or "http://127.0.0.1:4723"

    def create_driver(self, role: str) -> webdriver.Remote:
        caps = merged_appium_capabilities(role)
        options = _options_from_caps(caps)
        return webdriver.Remote(command_executor=self._server_url, options=options)


def _options_from_caps(caps: dict[str, Any]) -> UiAutomator2Options:
    options = UiAutomator2Options()
    for key, value in caps.items():
        if value is None:
            continue
        options.set_capability(str(key), value)
    return options
