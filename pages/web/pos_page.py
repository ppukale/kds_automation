from __future__ import annotations

from typing import Any

from playwright.sync_api import Page

from actions.web_actions import WebActions
from utils.config_loader import load_env
from utils.logger import setup_logging


class PosPage:
    """POS ordering surface — replace selectors with your real app."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.actions = WebActions(page)
        self._log = setup_logging(__name__)
        env = load_env()
        web = env.get("web") or {}
        self._base_url = web.get("base_url") or "about:blank"

    def open(self) -> None:
        self.page.goto(self._base_url)

    def place_order_from_data(self, order: dict[str, Any]) -> None:
        """Drive POS UI from test data. Implement SKU / menu steps per your selectors."""
        self.open()
        items = order.get("items") or []
        self._log.info("Placing web order: %s item row(s)", len(items))
        # TODO: map each item SKU to menu actions, checkout, pay.


    # Example stubs — adjust locators to match your POS UI
    def cart_button(self):
        return self.page.get_by_role("button", name="Cart")

    def add_item_named(self, name: str):
        return self.page.get_by_role("button", name=name)
