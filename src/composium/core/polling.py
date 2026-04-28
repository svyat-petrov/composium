from __future__ import annotations

import logging
import time
import typing as t

from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT: t.Final = 10.0
DEFAULT_DELAY: t.Final = 0.5


class PollingConfig:
    """Configurable polling parameters for element lookup.

    Usage:
        config = PollingConfig(timeout=15.0, delay=1.0)
        # Or use defaults:
        config = PollingConfig()
    """

    def __init__(self, *, timeout: float = DEFAULT_TIMEOUT, delay: float = DEFAULT_DELAY) -> None:
        if timeout <= 0:
            raise ValueError(f'timeout must be positive, got {timeout}')
        if delay <= 0:
            raise ValueError(f'delay must be positive, got {delay}')

        self._timeout = timeout
        self._delay = delay

    @property
    def timeout(self) -> float:
        return self._timeout

    @property
    def delay(self) -> float:
        return self._delay

    def __repr__(self) -> str:
        return f'PollingConfig(timeout={self._timeout}, delay={self._delay})'


CatchType = type[BaseException] | tuple[type[BaseException], ...]


def poll(func: t.Callable[[], t.Any], *, config: PollingConfig, catch: CatchType = NoSuchElementException) -> t.Any:
    """Call func with retry loop until timeout or success.

    Args:
        func: Callable that may raise an exception from catch list.
        config: Polling parameters (timeout, delay).
        catch: Exception types to catch and retry on.

    Returns:
        Result of successful func() call.

    Raises:
        NoSuchElementException: Re-raised with context if all retries fail.
    """
    last_error: BaseException | None = None
    start_time = time.monotonic()

    while time.monotonic() - start_time <= config.timeout:
        try:
            return func()
        except catch as exc:
            last_error = exc
            logger.debug(
                f'Polling retry: {exc} '
                f'(elapsed={time.monotonic() - start_time:.1f}s, '
                f'timeout={config.timeout}s)'
            )
            time.sleep(config.delay)

    raise NoSuchElementException(
        f'Element not found after polling (timeout={config.timeout}s, delay={config.delay}s)'
    ) from last_error
