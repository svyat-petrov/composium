from __future__ import annotations

import typing as t

from appium.webdriver.webdriver import WebDriver


def is_android(driver: WebDriver) -> bool:
    """Check if the driver is connected to an Android device."""
    return _get_platform_name(driver) == 'android'


def is_ios(driver: WebDriver) -> bool:
    """Check if the driver is connected to an iOS device."""
    return _get_platform_name(driver) == 'ios'


def _get_platform_name(driver: WebDriver) -> str:
    """Extract normalized platform name from driver capabilities."""
    capabilities = driver.capabilities or {}
    platform = t.cast(str, capabilities.get('platformName', ''))
    return platform.strip().lower()
