from __future__ import annotations

from typing import TYPE_CHECKING

from appium import webdriver

from drivers.appium_driver import AppiumDriverFactory

if TYPE_CHECKING:
    pass


class DeviceManager:
    """Keeps one Appium session per logical tablet role."""

    def __init__(self, factory: AppiumDriverFactory | None = None) -> None:
        self._factory = factory or AppiumDriverFactory()
        self._drivers: dict[str, webdriver.Remote] = {}

    def get(self, role: str) -> webdriver.Remote:
        if role not in self._drivers:
            self._drivers[role] = self._factory.create_driver(role)
        return self._drivers[role]

    def quit(self, role: str) -> None:
        driver = self._drivers.pop(role, None)
        if driver:
            driver.quit()

    def quit_all(self) -> None:
        for role in list(self._drivers.keys()):
            self.quit(role)
