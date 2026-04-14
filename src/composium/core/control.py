from selenium.webdriver.remote.webelement import WebElement


class Control(WebElement):
    """Base control class. Extends WebElement with interaction methods.

    Controls are bound to WebElements dynamically via __class__ reassignment
    in LazyElement._bind_control(). This allows adding platform-specific
    behavior (e.g., InputControl with clear_input, focus) without wrapping.
    """
    pass