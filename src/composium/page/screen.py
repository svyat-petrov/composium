from __future__ import annotations

import typing as t

import attrs

from .base_page import BasePage


@attrs.define
class ScreenMeta:
    """Metadata for Screen: name for reporting, deeplink for navigation."""
    name: str | None = attrs.field(default=None)
    deeplink: str | None = attrs.field(default=None)


class Screen(BasePage):
    """Top-level page object representing a full application screen.

    Screen is a composition of Widgets via Embedded.
    Its parent is always the WebDriver (Appium driver).

    Usage:
        @define.screen(name="Cart", deeplink="myapp://cart?id={product_id}")
        class CartScreen(Screen):
            payment = Embedded(PaymentWidget)
            receiver = Embedded(ReceiverWidget)
    """

    __meta__: t.ClassVar[ScreenMeta] = ScreenMeta()

    @property
    def meta(self) -> ScreenMeta:
        """Screen metadata: name and optional deeplink."""
        return self.__meta__

