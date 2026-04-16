from __future__ import annotations

import typing as t

import attrs
from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..core.query import Locator, Query
from .base_page import BasePage


@attrs.define()
class WidgetMeta:
    """Metadata for Widget: name for reporting, parent locator for scoping."""
    name: str | None = attrs.field(default=None)
    parent: Locator | str | None = attrs.field(default=None)


class Widget(BasePage):
    """Represents a logical UI block (payment form, receiver list, etc.).

    Widget has its own root element defined by meta.parent.
    All child Element lookups are scoped to this root, not the entire screen.

    This is the key to multi-level POM: Screen contains Widgets,
    Widgets contain Items and Elements, each scoped to its own DOM subtree.

    Usage:
        @define.widget(name="PaymentMethods", parent="id::payment_root")
        class PaymentWidget(Widget):
            _title = Element("id::payment_title")
            _methods = Element("xpath::...", multiple=True, item=PaymentMethodItem)
    """

    __meta__: t.ClassVar[WidgetMeta] = WidgetMeta()

    @property
    def meta(self) -> WidgetMeta:
        """Widget metadata: name and parent locator."""
        return self.__meta__

    @property
    def parent(self) -> WebDriver | WebElement:
        """Resolve parent: if meta.parent is set, find root element within _parent."""
        if self.meta.parent is not None:
            result = Query(self.meta.parent, multiple=False).execute(self._parent)
            if isinstance(result, WebElement):
                return result
            raise TypeError(
                f"Widget parent locator must resolve to a single WebElement, "
                f"got {type(result).__name__}"
            )
        return self._parent


