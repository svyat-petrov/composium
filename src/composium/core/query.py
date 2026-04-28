from __future__ import annotations

import typing as t

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


class Locator:
    """Parsed locator strategy with by/value pair

    Supports string format: 'strategy::value'
    Examples:
        'id::my_button'
        'xpath:://*[@text="Submit"]'
        'accessibility-id::login_button'
        'name::search_field'
    """

    _STRATEGY_MAP: t.ClassVar[dict[str, str]] = {
        'id': By.ID,
        'xpath': By.XPATH,
        'css': By.CSS_SELECTOR,
        'name': By.NAME,
        'accessibility-id': AppiumBy.ACCESSIBILITY_ID,
        'class': By.CLASS_NAME,
    }

    def __init__(self, by: str, value: str):
        self._by = by
        self._value = value

    @classmethod
    def from_string(cls, raw: str) -> Locator:
        """
        Parse 'strategy::value' string into Locator
        Falls back to xpath if '/' detected, otherwise to id
        """

        if '::' in raw:
            strategy, value = raw.split('::', maxsplit=1)
            by = cls._STRATEGY_MAP.get(strategy)
            if by is None:
                raise ValueError(
                    f'Unknown locator strategy "{strategy}".'
                    f'Supported: {list(cls._STRATEGY_MAP.keys())}'
                )
            return cls(by=by, value=value)

        if raw.startswith('/'):
            return cls(by=By.XPATH, value=raw)

        return cls(by=By.ID, value=raw)

    @property
    def by(self) -> str:
        """Return the search strategy (e.g., 'id', 'xpath')."""
        return self._by

    @property
    def value(self) -> str:
        """Return the search value."""
        return self._value

    def __repr__(self) -> str:
        return f'Locator({self._by}={self._value})'


class Query:
    """
    Executes element search using Selector against a parent (driver or element).

    Supports single and multiple element lookup, with optional wrapping
    (e.g., wrapping raw WebElements into Item instances).
    """

    def __init__(
        self,
        locator: Locator | str,
        *,
        multiple: bool = False,
        wrap: t.Callable[[WebElement], t.Any] | None = None,
    ):
        final_locator = Locator.from_string(locator) if isinstance(locator, str) else locator
        self._locator = final_locator
        self._multiple = multiple
        self._wrap = wrap

    @property
    def locator(self) -> Locator:
        """Return the parsed Locator object."""
        return self._locator

    @property
    def multiple(self) -> bool:
        """Return True if searching for multiple elements."""
        return self._multiple

    def execute(self, parent: WebDriver | WebElement) -> WebElement | list[WebElement] | t.Any:
        """Find element(s) using the stored locator against the given parent."""

        if self._multiple:
            return self._find_all(parent)
        return self._find_one(parent)

    def _find_one(self, parent: WebDriver | WebElement) -> WebElement | t.Any:
        """Find a single element, applying wrap function if provided."""
        try:
            element = parent.find_element(self._locator.by, self._locator.value)
        except NoSuchElementException:
            raise NoSuchElementException(f'Element not found: {self._locator}') from None

        if self._wrap is not None:
            return self._wrap(element)
        return element

    def _find_all(self, parent: WebDriver | WebElement) -> list[t.Any]:
        """Find multiple elements, applying wrap function to each if provided."""
        elements = parent.find_elements(self._locator.by, self._locator.value)

        if self._wrap is not None:
            return [self._wrap(element) for element in elements]

        return elements
