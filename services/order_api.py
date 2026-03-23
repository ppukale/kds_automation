from __future__ import annotations

from typing import Any

import requests

from utils.config_loader import load_env


def orders_submit_url() -> str:
    env = load_env()
    api = env.get("api") or {}
    return str(api.get("orders_submit_url") or "").strip()


def submit_order_via_api(order: dict[str, Any]) -> requests.Response:
    """POST JSON order to backend. Configure api.orders_submit_url in config/env.yaml."""
    url = orders_submit_url()
    if not url:
        raise RuntimeError(
            "API channel selected but api.orders_submit_url is empty. "
            "Set it in config/env.yaml (or config/local.yaml)."
        )
    timeout_s = float((load_env().get("api") or {}).get("timeout_s") or 60)
    response = requests.post(url, json=order, timeout=timeout_s)
    response.raise_for_status()
    return response
