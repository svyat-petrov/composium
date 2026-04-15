from __future__ import annotations

import typing as t

from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class BasePage:
    """Foundation class for all page objects (Screen, Widget, Item).

    Provides:
    - parent: search context (WebDriver or WebElement) for child element lookup
    - driver: resolved WebDriver instance (walks up the parent chain if needed)

    All Element descriptors use instance.parent as the search root.
    """
    def __init__(self, parent: WebDriver | WebElement) -> None:
        self._parent = parent


    @property
    def parent(self) -> WebDriver | WebElement:
        """Search context for child element lookup."""
        return self._parent


    @property
    def driver(self) -> WebDriver:
        """Resolved WebDriver instance by walking up the parent chain."""
        return _resolve_driver(self._parent)


def _resolve_driver(context: t.Any) -> WebDriver:
    """Recursively resolve WebDriver from a parent chain.

    WebDriver → returned directly
    WebElement → WebElement.parent (reference to WebDriver in Selenium)
    BasePage → walk up via _parent attribute

    Raises:
        TypeError: if WebDriver cannot be resolved from the chain.
    """
    if isinstance(context, WebDriver):
        return context

    if isinstance(context, WebElement):
        return t.cast(WebDriver, context.parent)

    if hasattr(context, '_parent'):
        return _resolve_driver(getattr(context, '_parent'))

    raise TypeError(
        f"Cannot resolve WebDriver from {type(context).__name__}. "
        f"Expected WebDriver, WebElement, or BasePage subclass in the parent chain."
    )

