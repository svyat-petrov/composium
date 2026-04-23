from __future__ import annotations

import logging
from datetime import datetime

from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException

from .reporter import get_reporter

logger = logging.getLogger(__name__)


def _timestamped_name(prefix: str, extension: str) -> str:
    """Generate a timestamped filename for diagnostic attachments."""
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f'{prefix}_{now}.{extension}'


def attach_failure_diagnostics(driver: WebDriver) -> None:
    """Attach screenshot and page_source to the reporter on element lookup failure.

    Catches WebDriverException only — driver-level errors are ignored.
    Errors in reporting itself will propagate.
    """
    reporter = get_reporter()
    try:
        screenshot = driver.get_screenshot_as_png()
        reporter.attach(screenshot, name=_timestamped_name('screenshot', 'png'), attachment_type='png')
    except WebDriverException:
        logger.debug('Failed to attach screenshot on failure')

    try:
        page_source = driver.page_source
        reporter.attach(
            page_source,
            name=_timestamped_name('page_source', 'xml'),
            attachment_type='text',
        )
    except WebDriverException:
        logger.debug('Failed to attach page_source on failure')
