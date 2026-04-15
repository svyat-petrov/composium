"""Page elements — declarative descriptors for building Page Objects.

Usage:
    from composium.page_elements import Element, Button, Input, Embedded

    class CheckoutScreen(Screen):
        _pay_button = Button("id::pay_button")
        _email = Input("id::email_input")
        payment_form = Embedded(PaymentWidget)
"""

from .cross_platform import CrossPlatformElement
from .element import Button, Element, Input
from .embedded import Embedded

__all__ = [
    "Element",
    "Button",
    "Input",
    "Embedded",
    "CrossPlatformElement",
]
