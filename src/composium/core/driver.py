from __future__ import annotations

import typing as t

from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


def resolve_driver(context: t.Any) -> WebDriver | None:
    """Resolve WebDriver from a parent chain.

    WebDriver → returned directly
    WebElement → WebElement.parent (reference to WebDriver in Selenium)
    Any object with _parent → walk up the chain

    Returns:
        WebDriver instance or None if resolution fails.
    """
    while context is not None:
        if isinstance(context, WebDriver):
            return context
        if isinstance(context, WebElement):
            return t.cast(WebDriver, context.parent)
        if hasattr(context, '_parent'):
            context = context._parent
        else:
            return None
    return None
