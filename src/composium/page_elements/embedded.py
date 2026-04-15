from __future__ import annotations

import typing as t

from ..core.query import Locator, Query

if t.TYPE_CHECKING:
    from ..page.base_page import BasePage


class Embedded:
    """Descriptor that instantiates a nested page object (Widget, Item) on access.

    Unlike Element (which creates LazyElement), Embedded creates
    a full page object instance, enabling multi-level composition:
    Screen → Widget → nested Widget.

    Usage:
        class CheckoutScreen(Screen):
            payment_widget = Embedded(PaymentWidget)
            receiver_widget = Embedded(ReceiverWidget)
    """

    def __init__(
            self,
            page_class: type[BasePage],
            parent: Locator | str | None = None
    ):
        self._page_class = page_class
        self._parent_locator = parent


    def __get__(self, instance: BasePage | None, owner: type) -> t.Any:
        """Instantiate nested page object with resolved parent."""
        if instance is None:
            return self

        parent = instance.parent

        if self._parent_locator is not None:
            parent = Query(self._parent_locator).execute(parent)

        return self._page_class(parent)
