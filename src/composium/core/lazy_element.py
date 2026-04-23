from __future__ import annotations

import logging
import typing as t

from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement

from .diagnostics import attach_failure_diagnostics
from .driver import resolve_driver
from .element_mixin import ElementMixin
from .polling import PollingConfig, poll
from .query import Query

logger = logging.getLogger(__name__)

ElementOrList = t.Union[WebElement, list[WebElement], t.Any, list[t.Any]]

class LazyElement:
    """Proxy object that locates element(s) lazily — only when accessed.

    Supports:
    - Attribute forwarding to underlying WebElement (__getattr__)
    - Iteration over multiple elements (__iter__)
    - Indexing into element collections (__getitem__)
    - Callable behavior for actions like click (__call__)
    - Configurable polling with retry on NoSuchElementException
    - Automatic screenshot + page_source attachment on failure
    - ElementMixin injection for custom interaction methods
    """

    def __init__(
            self,
            query: Query,
            parent: WebDriver | WebElement,
            *,
            call: t.Callable[[LazyElement], t.Callable] | None = None,
            mixin: type[ElementMixin] | None = None,
            polling_timeout: float = 5.0,
    ):
        self._query = query
        self._parent = parent
        self._call = call
        self._mixin = mixin
        self._polling = polling
        self._cached_element: ElementOrList | None = None


    def __repr__(self) -> str:
        locator = self._query.locator
        base = f"LazyElement({locator.by}='{locator.value}', multiple={self._query.multiple})"
        if self._cached_element is not None:
            return f"{base} -> {self._cached_element}"
        return base


    def __call__(self, *args, **kwargs) -> t.Any:
        if self._call is not None:
            return self._call(self)(*args, **kwargs)
        raise TypeError(f"{self!r} is not callable")


    def __iter__(self) -> t.Iterator:
        self._ensure_loaded()
        if isinstance(self._cached_element, list):
            return iter(self._cached_element)
        raise TypeError(f"{self!r} is not iterable (single element)")


    def __getitem__(self, index: int) -> WebElement | t.Any:
        self._ensure_loaded()
        if not isinstance(self._cached_element, list):
            raise TypeError(f"{self!r} is not subscriptable (single element)")
        if not (0 <= index < len(self._cached_element)):
            self._attach_diagnostics()
            raise IndexError(
                f"Index {index} out of range. "
                f"Available elements: {len(self._cached_element)}. "
                f"Locator: {self._query.locator}"
            )
        return self._cached_element[index]


    def __getattr__(self, name: str) -> t.Any:
        if name.startswith('_'):
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{name}'")
        self._ensure_loaded()
        return getattr(self._cached_element, name)


    @property
    def query(self) -> Query:
        return self._query

    @property
    def parent(self) -> WebDriver | WebElement:
        return self._parent

    @property
    def polling(self) -> PollingConfig:
        """Return polling config, falling back to default if not set."""
        if self._polling is None:
            return PollingConfig()
        return self._polling

    @property
    def count(self) -> int:
        """Return number of found elements. 0 if not found, 1 if single."""
        self._ensure_loaded()
        if self._cached_element is None:
            return 0
        if isinstance(self._cached_element, list):
            return len(self._cached_element)
        return 1


    def load(self, *, reload: bool = False) -> None:
        """Execute query and cache the result. Optionally force reload."""
        if reload:
            self._cached_element = None

        if self._cached_element is None:
            self._cached_element = self._query.execute(self._parent)
            if self._mixin is not None:
                self._bind_mixin()


    def exists(self) -> bool:
        """Check if element exists without raising. Returns bool."""
        self._cached_element = None
        try:
            self.load()
            return True
        except (NoSuchElementException, WebDriverException):
            return False


    def _ensure_loaded(self) -> None:
        """Load element with configurable polling retry."""
        try:
            self.load()
        except NoSuchElementException:
            try:
                poll(
                    lambda: self.load(reload=True),
                    config=self.polling,
                    catch=NoSuchElementException,
                )
            except NoSuchElementException:
                self._attach_diagnostics()
                raise AssertionError(
                    f"Element not found after polling {self.polling}: "
                    f"{self._query.locator}"
                ) from None

    def _bind_mixin(self) -> None:
        """Dynamically reassign WebElement's class to include Control methods."""

        mixin_cls = self._mixin

        def bind(elem: WebElement) -> None:
            assert mixin_cls is not None
            elem.__class__ = type(
                mixin_cls.__name__,
                (mixin_cls,) + type(elem).__mro__,
                {}
            )

        if isinstance(self._cached_element, list):
            for element in self._cached_element:
                if isinstance(element, WebElement):
                    bind(element)
        elif isinstance(self._cached_element, WebElement):
            bind(self._cached_element)

    def _attach_diagnostics(self) -> None:
        """Attach screenshot and page_source to the reporter on failure."""
        driver = resolve_driver(self._parent)
        if driver is not None:
            attach_failure_diagnostics(driver)
