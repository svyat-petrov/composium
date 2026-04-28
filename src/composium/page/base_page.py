from __future__ import annotations

from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..core.driver import resolve_driver


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
        driver = resolve_driver(self._parent)
        if driver is not None:
            return driver
        raise TypeError(
            f'Cannot resolve WebDriver from {type(self._parent).__name__}. '
            f'Expected WebDriver, WebElement, or BasePage subclass in the parent chain.'
        )
