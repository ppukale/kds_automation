from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    backoff_s: float = 0.5,
    on_exception: type[BaseException] | tuple[type[BaseException], ...] = Exception,
) -> T:
    last: BaseException | None = None
    for i in range(attempts):
        try:
            return fn()
        except on_exception as exc:  # noqa: PERF203
            last = exc
            if i == attempts - 1:
                break
            time.sleep(backoff_s * (2**i))
    assert last is not None
    raise last
