from __future__ import annotations

import functools
import typing as t

import allure


def step(title: str) -> t.Callable:
    """Wrap a method as an Allure step with the given title."""
    def decorator(func: t.Callable) -> t.Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> t.Any:
            with allure.step(title):
                return func(*args, **kwargs)
        return wrapper
    return decorator
