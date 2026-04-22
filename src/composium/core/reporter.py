from __future__ import annotations

import typing as t
from contextlib import contextmanager


class ReporterProtocol(t.Protocol):
    """Protocol for reporting integrations (Allure, ReportPortal, etc.)."""
    def step(self, message: str) -> t.ContextManager[None]:
        ...

    def attach(self, body: str | bytes, *, name: str | None = None, attachment_type: str | None = None) -> None:
        ...

    def epic(self, *epics: str) -> None:
        ...

    def story(self, *stories: str) -> None:
        ...

    def feature(self, *features: str) -> None:
        ...

class WithoutReporter:
    """No-op reporter. Used when no reporting integration is configured."""
    @contextmanager
    def step(self, _message: str) -> t.Iterator[None]:
        yield

    def attach(self, body: str | bytes, *, name: str | None = None, attachment_type: str | None = None) -> None:
        pass

    def epic(self, *epics: str) -> None:
        pass

    def story(self, *stories: str) -> None:
        pass

    def feature(self, *features: str) -> None:
        pass

_reporter: ReporterProtocol = WithoutReporter()

def configure_reporter(reporter: ReporterProtocol) -> None:
    """Set the global reporter instance.

    Built-in adapters:
        import allure
        import composium

        composium.configure_reporter(composium.AllureReporter(allure))

    Custom adapter (any class with step/attach/epic/story/feature methods):
        class MyReporter:
            def step(self, message): ...
            def attach(self, body, *, name=None, attachment_type=None): ...
            def epic(self, *epics): ...
            def story(self, *stories): ...
            def feature(self, *features): ...

        composium.configure_reporter(MyReporter())
    """
    global _reporter
    _reporter = reporter

def get_reporter() -> ReporterProtocol:
    """Return the current global reporter instance."""
    return _reporter


class AllureReporter:
    """Allure integration adapter.

    Usage:
        import allure
        import composium

        composium.configure_reporter(composium.AllureReporter(allure))
    """
    def __init__(self, allure_module: t.Any) -> None:
        self._allure = allure_module

    @contextmanager
    def step(self, message: str) -> t.Iterator[None]:
        with self._allure.step(message):
            yield

    def attach(self, body: str | bytes, *, name: str | None = None, attachment_type: str | None = None) -> None:
        self._allure.attach(body, name=name, attachment_type=attachment_type)

    def epic(self, *epics: str) -> None:
        self._allure.epic(*epics)

    def story(self, *stories: str) -> None:
        self._allure.story(*stories)

    def feature(self, *features: str) -> None:
        self._allure.feature(*features)
