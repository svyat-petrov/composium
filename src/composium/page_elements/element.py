from __future__ import annotations

import typing as t

from ..core.element_mixin import ElementMixin
from ..core.lazy_element import LazyElement
from ..core.polling import PollingConfig
from ..core.query import Locator, Query

if t.TYPE_CHECKING:
    from ..page.base_page import BasePage


class Element:
    """Descriptor that creates LazyElement when accessed on a page object instance.

    Usage:
        class MyWidget(Widget):
            _button = Element("id::submit_button")
            _items = Element("xpath:://*[@class='item']", multiple=True)
            _input = Element("id::email_input", mixin=InputMixin)
    """

    def __init__(
            self,
            locator: Locator | str,
            *,
            multiple: bool = False,
            item: type[BasePage] | None = None,
            mixin: type[ElementMixin] | None = None,
            polling: PollingConfig | None = None
    ):
        self._query = Query(
            locator,
            multiple=multiple,
            wrap=item
        )
        self._mixin = mixin
        self._polling = polling


    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}"
            f"({self._query.locator.by}='{self._query.locator.value}')>"
        )

    def __get__(self, instance: BasePage | None, owner: type) -> LazyElement | Element:
        if instance is None:
            return self
        return self._create_lazy_element(instance.parent)


    @property
    def query(self) -> Query:
        return self._query


    def _create_lazy_element(self, parent: t.Any) -> LazyElement:
        """Create instance LazyElement with stored query, mixin, polling and parent."""
        return LazyElement(
            self._query,
            parent,
            mixin=self._mixin,
            polling=self._polling
        )


class Button(Element):
    """Element for clickable components — buttons, links, cards.

    Semantic alias — behaves identically to Element,
    but signals intent in page object declarations.
    """


class Input(Element):
    """Element for text input components — text fields, text areas."""
