from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def poll_until(
    fn: Callable[[], T | None],
    *,
    timeout_s: float = 30.0,
    interval_s: float = 0.25,
    description: str = "condition",
) -> T:
    """Poll fn until it returns a non-None value or timeout."""
    end = time.monotonic() + timeout_s
    last_exc: Exception | None = None
    while time.monotonic() < end:
        try:
            result = fn()
            if result is not None:
                return result
        except Exception as exc:  # noqa: BLE001 — polling boundary
            last_exc = exc
        time.sleep(interval_s)
    if last_exc:
        raise TimeoutError(f"Timed out waiting for {description}") from last_exc
    raise TimeoutError(f"Timed out waiting for {description}")
