from selenium.webdriver.remote.webelement import WebElement


class ElementMixin(WebElement):
    """Base mixin class. Extends WebElement with interaction methods.

    ElementMixin subclasses are injected via __class__ reassignment
    in LazyElement._bind_control(). This allows adding platform-specific
    behavior (e.g., InputControl with clear_input, focus) without wrapping.
    """
    pass
