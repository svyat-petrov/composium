"""Declarative DSL — decorators for page objects and their methods.

Usage:
    from composium.decorators import define

    @define.screen(name="Checkout", deeplink="myapp://checkout")
    class CheckoutScreen(Screen): ...

    @define.widget(name="Payment", parent="id::payment_root")
    class PaymentWidget(Widget): ...

    @define.item("PaymentMethod")
    class PaymentMethodItem(Item): ...

    @define.action("select payment method")
    def select_method(self, title: str): ...

    @define.assertion("payment widget is displayed")
    def is_displayed(self): ...
"""

from __future__ import annotations

import typing as t

from ..core.query import Locator
from ..page.item import Item, ItemMeta
from ..page.screen import Screen, ScreenMeta
from ..page.widget import Widget, WidgetMeta
from .reporting import step


def action(title: str) -> t.Callable:
    """Mark a method as a user-facing action with Allure step reporting.
    Actions represent user interactions: tap, select, fill, scroll.
    """
    return step(f"Action: {title}")


def assertion(title: str) -> t.Callable:
    """Mark a method as a verification step with Allure step reporting.
    Assertions represent checks: is_displayed, has_items, verify_text.
    """
    return step(f"Assert: {title}")


def widget(name: str, *, parent: Locator | str | None = None) -> t.Callable[[type[Widget]], type[Widget]]:
    """Attach WidgetMeta to a Widget class."""

    def decorator(cls: type[Widget]) -> type[Widget]:
        cls.__meta__ = WidgetMeta(name=name, parent=parent)
        return cls

    return decorator


def item(name: str) -> t.Callable[[type[Item]], type[Item]]:
    """Attach ItemMeta to an Item class."""

    def decorator(cls: type[Item]) -> type[Item]:
        cls.__meta__ = ItemMeta(name=name)
        return cls

    return decorator


def screen(name: str, *, deeplink: str | None = None) -> t.Callable[[type[Screen]], type[Screen]]:
    """Attach ScreenMeta to a Screen class."""

    def decorator(cls: type[Screen]) -> type[Screen]:
        cls.__meta__ = ScreenMeta(name=name, deeplink=deeplink)
        return cls

    return decorator
