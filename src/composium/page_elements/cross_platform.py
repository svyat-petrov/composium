from __future__ import annotations

import typing as t

from ..utils.platform import is_android, is_ios
from .element import Element

if t.TYPE_CHECKING:
    from ..page.base_page import BasePage


class CrossPlatformElement:
    """Descriptor that selects the correct Element based on the active driver platform.

    Automatically detects Android or iOS driver and returns
    the corresponding Element's LazyElement.

    Usage:
        class ReceiverItem(Item):
            _name = CrossPlatformElement(
                android=Element("id::receiver_name"),
                ios=Element("accessibility-id::receiver_name")
            )
    """
    def __init__(self, *, android: Element, ios: Element):
        self._android = android
        self._ios = ios
        self._attr_name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Capture attribute name for error messages."""
        self._attr_name = name

    def __get__(self, instance: BasePage | None, owner: type) -> t.Any:
        """Resolve platform and delegate to the correct Element."""
        if instance is None:
            return self

        element = self._resolve_element(instance)
        return element.__get__(instance, owner)

    def _resolve_element(self, instance: BasePage) -> Element:
        """Detect platform from driver and return matching Element."""
        driver = instance.driver

        if is_android(driver):
            return t.cast(Element, self._android)
        if is_ios(driver):
            return t.cast(Element, self._ios)

        raise AttributeError(
            f"CrossPlatformElement '{self._attr_name}' cannot resolve platform "
            f"for driver '{driver.__class__.__name__}'. "
            f"Expected Android or iOS driver."
        )

    @classmethod
    def from_id(cls, element_id: str, *, element_class: type[Element] = Element) -> CrossPlatformElement:
        """Create CrossPlatformElement with id (Android) and accessibility-id (iOS)."""
        return cls(
            android=element_class(f'id::{element_id}'),
            ios=element_class(f'accessibility-id::{element_id}'),
        )
