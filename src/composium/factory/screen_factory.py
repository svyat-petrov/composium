from __future__ import annotations

import typing as t

from appium.webdriver.webdriver import WebDriver

from ..page.screen import Screen


class ScreenFactory:
    """Factory for creating Screen instances with optional deeplink navigation.

    Usage:
        factory = ScreenFactory(driver)
        checkout = factory(CheckoutScreen, product_id="123", sku_id="456")
    """

    def __init__(self, driver: WebDriver):
        self._driver = driver

    def __call__(self, screen_class: type[Screen], **deeplink_kwargs: t.Any) -> Screen:
        screen = screen_class(self._driver)

        deeplink = screen.meta.deeplink
        if deeplink is not None and deeplink_kwargs:
            deeplink = deeplink.format(**deeplink_kwargs)

        if deeplink is not None:
            self._driver.get(deeplink)

        return screen
