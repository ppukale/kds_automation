from __future__ import annotations

from utils.config_loader import load_env


def configured_web_base_url() -> str | None:
    """Returns POS base URL if set to a non-placeholder value, else None."""
    env = load_env()
    web = env.get("web") or {}
    raw = str(web.get("base_url") or "").strip()
    if not raw or raw == "about:blank":
        return None
    lower = raw.lower()
    if "example.local" in lower or "pos.example.local" in lower:
        return None
    return raw


def web_base_url_skip_reason() -> str:
    return (
        "Set web.base_url in config/env.yaml (or config/local.yaml) to your real POS URL. "
        "The placeholder https://pos.example.local/ does not resolve (ERR_NAME_NOT_RESOLVED)."
    )
