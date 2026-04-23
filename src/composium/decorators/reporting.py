from __future__ import annotations

import functools
import typing as t

from ..core.reporter import get_reporter


def step(title: str) -> t.Callable:
    """Wrap a method as a reporter step with the given title.

    Uses the globally configured reporter (WithoutReporter by default).
    Configure with composium.configure_reporter() before tests.
    """
    def decorator(func: t.Callable) -> t.Callable:
        @functools.wraps(func)
        def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            with get_reporter().step(title):
                return func(*args, **kwargs)
        return wrapper
    return decorator
