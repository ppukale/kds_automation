from __future__ import annotations

from typing import Any

import yaml

from utils.config_loader import load_env, project_root

_CONFIG_PATH = project_root() / "data" / "kitchen_station_rules.yaml"


def load_kitchen_station_rules() -> dict[str, Any]:
    with _CONFIG_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("kitchen_station_rules.yaml must be a mapping.")
    return data


def _tags(item: dict[str, Any]) -> set[str]:
    raw = item.get("tags")
    if raw is None:
        return set()
    if isinstance(raw, str):
        return {raw.strip()}
    if isinstance(raw, list):
        return {str(t).strip() for t in raw if t is not None}
    return set()


def partition_order_for_stations(order: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return line items that should appear on each station based on tags × rules."""
    rules = load_kitchen_station_rules()
    sets_map = rules.get("station_tag_sets") or {}
    items = order.get("items") or []
    if not isinstance(items, list):
        return {k: [] for k in ("gunner", "bombardier", "wingman", "pilot")}

    gunner_tags = set(sets_map.get("gunner") or [])
    bombardier_tags = set(sets_map.get("bombardier") or [])
    wingman_tags = set(sets_map.get("wingman") or [])

    gunner: list[dict[str, Any]] = []
    bombardier: list[dict[str, Any]] = []
    wingman: list[dict[str, Any]] = []

    for it in items:
        if not isinstance(it, dict):
            continue
        tags = _tags(it)
        if tags & gunner_tags:
            gunner.append(it)
        if tags & bombardier_tags:
            bombardier.append(it)
        if tags & wingman_tags:
            wingman.append(it)

    pilot_items = list(items) if items else []

    return {
        "gunner": gunner,
        "bombardier": bombardier,
        "wingman": wingman,
        "pilot": pilot_items,
    }


def display_key_for_assertion(item: dict[str, Any]) -> str:
    """Text to look for on KDS (prefer human label, else SKU)."""
    for key in ("display_name", "label", "name", "sku"):
        val = item.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def order_number_from_order(order: dict[str, Any]) -> str | None:
    """Ticket / order id expected on KDS headers."""
    for key in ("order_number", "order_id", "ticket_number", "ticket_id"):
        val = order.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def _kitchen_format() -> str:
    env = load_env()
    k = env.get("kitchen") or {}
    return str(k.get("line_text_format") or "{qty}x {name}")


def line_display_text_for_assertion(item: dict[str, Any]) -> str:
    """
    Full line as shown on KDS: quantity + item label, unless item provides kds_line_text.
    Set kds_line_text to match your UI exactly (e.g. '2× Large Fries').
    """
    override = item.get("kds_line_text")
    if override is not None and str(override).strip():
        return str(override).strip()

    name = display_key_for_assertion(item)
    if not name:
        return ""

    qty_raw = item.get("qty")
    if qty_raw is None:
        qty = 1
    else:
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            return name

    fmt = _kitchen_format()
    sku = str(item.get("sku") or "").strip()
    try:
        return fmt.format(qty=qty, name=name, sku=sku)
    except (KeyError, ValueError):
        return f"{qty}x {name}"


def line_display_strings_for_items(items: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        text = line_display_text_for_assertion(it)
        if text:
            out.append(text)
    return out
