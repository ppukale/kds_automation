from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils.config_loader import project_root


def load_orders_document() -> dict[str, Any]:
    path = project_root() / "data" / "orders.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("orders.json must be a JSON object at root.")
    return data


def load_order_profile(profile_key: str) -> dict[str, Any]:
    doc = load_orders_document()
    if profile_key not in doc:
        available = ", ".join(sorted(doc.keys()))
        raise KeyError(
            f"Unknown order profile {profile_key!r}. Available: {available}"
        )
    profile = doc[profile_key]
    if not isinstance(profile, dict):
        raise ValueError(f"Order profile {profile_key!r} must be an object.")
    return profile
