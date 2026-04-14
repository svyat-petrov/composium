from __future__ import annotations

import logging
import time
import typing as t

from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement

from .control import Control
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
    - Automatic retry on NoSuchElementException with configurable polling
    - Control binding for custom interaction methods
    """

    def __init__(
            self,
            query: Query,
            parent: WebDriver | WebElement,
            *,
            call: t.Callable[[LazyElement], t.Callable] | None = None,
            control: type[Control] | None = None,
            polling_timeout: float = 5.0,
    ):
        self._query = query
        self._parent = parent
        self._call = call
        self._control = control
        self._polling_timeout = polling_timeout
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
            if self._control is not None:
                self._bind_control()


    def exists(self) -> bool:
        """Check if element exists without raising. Returns bool."""
        self._cached_element = None
        try:
            self.load()
            return True
        except (NoSuchElementException, WebDriverException):
            return False


    def _ensure_loaded(self) -> None:
        """Load element with one retry after polling_timeout."""
        try:
            self.load()
        except NoSuchElementException:
            logger.debug(
                f"Element not found, retrying after {self._polling_timeout} second: "
                f"{self._query.locator}"
            )
            time.sleep(self._polling_timeout)
            try:
                self.load(reload=True)
            except NoSuchElementException:
                raise AssertionError(
                    f"Element not found after retry: {self._query.locator}"
                ) from None

    def _bind_control(self) -> None:
        """Dynamically reassign WebElement's class to include Control methods."""

        control_cls = self._control

        def bind(elem:WebElement) -> None:
            assert control_cls is not None
            elem.__class__ = type(
                control_cls.__name__,
                (control_cls,) + type(elem).__mro__,
                {}
            )

        if isinstance(self._cached_element, list):
            for element in self._cached_element:
                if isinstance(element, WebElement):
                    bind(element)
        elif isinstance(self._cached_element, WebElement):
            bind(self._cached_element)
