from __future__ import annotations

from selenium.webdriver.remote.webelement import WebElement

from .base_page import BasePage


class Item(BasePage):
    """Represents a single repeated element in a list/collection.

    Items are used with Element(multiple=True, item=MyItem).
    Each Item wraps one WebElement from the found collection
    and provides structured access to its child elements.

    Usage:
        class PaymentMethodItem(Item):
            title = Element("id::method_title")
            _radio = Element("id::method_radio")

            def select(self):
                self._radio.click()

        class PaymentWidget(Widget):
            _methods = Element("xpath::...", multiple=True, item=PaymentMethodItem)
    """
    def is_displayed(self) -> bool:
        """Check if the item's root element is displayed."""
        if isinstance(self._parent, WebElement):
            return self._parent.is_displayed()

        raise TypeError(
            f"Item parent must be WebElement, got {type(self._parent).__name__}"
        )
