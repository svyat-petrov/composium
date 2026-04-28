# composium — Documentation

Complete reference for the composium framework.
For a quick introduction, see [README.md](../README.md).

---

## Table of Contents

- [Core Concepts](#core-concepts)
  - [LazyElement](#lazyelement)
  - [Polling](#polling)
  - [Failure Diagnostics](#failure-diagnostics)
- [Page Object Hierarchy](#page-object-hierarchy)
  - [Screen](#screen)
  - [Widget](#widget)
  - [Item](#item)
- [Page Elements](#page-elements)
  - [Element](#element)
  - [Button / Input](#button--input)
  - [Embedded](#embedded)
  - [CrossPlatformElement](#crossplatforment)
- [Locator Syntax](#locator-syntax)
- [Decorator DSL](#decorator-dsl)
- [ScreenFactory](#screenfactory)
- [Reporter Integration](#reporter-integration)
- [Utilities](#utilities)

---

## Core Concepts

### LazyElement

`Element` is a Python descriptor. When accessed on a page object instance, it creates a `LazyElement` proxy. The actual `find_element` call is deferred until the element is used:

```python
class MyWidget(Widget):
    button = Element('id::submit')  # find_element not called yet

def test_something(my_widget):
    my_widget.button.click()  # find_element happens here
```

**LazyElement API:**

| Method / Property | Description |
|---|---|
| `click()`, `text`, `get_attribute()`, ... | Forwarded to the underlying `WebElement` via `__getattr__` |
| `__iter__` | Iterate over a collection of elements (when `multiple=True`) |
| `__getitem__(index)` | Access element by index from a collection |
| `count` | Number of found elements (0, 1, or length of list) |
| `reload()` | Force re-fetch the element from the driver |
| `exists()` | Check if element exists without raising (returns `bool`) |
| `polling` | `PollingConfig` for this element |

### Polling

Every element lookup includes automatic retry on `NoSuchElementException`.

**Default:** `PollingConfig(timeout=10.0, delay=0.5)`

Override per-element:

```python
from composium import Element, PollingConfig

_slow_element = Element(
    'xpath::.//*[contains(@text, "loading")]',
    polling=PollingConfig(timeout=15.0, delay=1.0),
)
```

> ⚠️ Global polling configuration is not yet implemented. Every element without an explicit `polling` parameter uses the default `PollingConfig()`. Project-wide override is planned — see Roadmap in README.

### Failure Diagnostics

When element lookup fails after all polling retries, composium automatically:
1. Takes a screenshot (`driver.get_screenshot_as_png()`)
2. Captures page source (`driver.page_source`)
3. Attaches both files without additional configuration (if Allure is enabled)

---

## Page Object Hierarchy

### Screen

Top-level page object representing a full application screen. Its `parent` is always `WebDriver`.

```python
from composium import Screen, Embedded
from composium.decorators import define

@define.screen(name='Home', deeplink='myapp://home?account_id={account_id}')
class HomeScreen(Screen):
    accounts = Embedded(AccountsWidget)
```

**ScreenMeta** (set by `@define.screen`):
- `name` — screen name
- `deeplink` — optional URL template for `ScreenFactory` navigation

### Widget

Logical UI block with its own root element. Child element lookups are scoped to this root, not the entire screen.

```python
from composium import Widget, Element, xpath_contains_id
from composium.decorators import define

@define.widget(name='Payment', parent=xpath_contains_id('payment_root'))
class PaymentWidget(Widget):
    _title = Element('id::payment_title')
    _methods = Element('xpath:://*[@class="method"]', multiple=True, item=PaymentMethodItem)
```

**WidgetMeta** (set by `@define.widget`):
- `name` — widget name
- `parent` — root element locator. When set, all child element lookups are scoped to this root element. When None, lookups start from the screen's driver.

### Item

Represents a single repeated element in a list/collection. Used with `Element(multiple=True, item=MyItem)`.

```python
from composium import Item, Element, CrossPlatformElement
from composium.decorators import define

@define.item('PaymentMethod')
class PaymentMethodItem(Item):
    title = Element('id::method_title')
    _radio = Element('id::method_radio')

    @define.action('select method')
    def select(self) -> None:
        self._radio.click()
```

**ItemMeta** (set by `@define.item`):
- `name` — item name (repeated element)

`Item` inherits from `BasePage` and provides `is_displayed()`, which delegates to the parent `WebElement.is_displayed()`.

## Page Elements

### Element

Python descriptor that creates `LazyElement` when accessed on a page object instance.

```python
from composium import Element, PollingConfig

class MyWidget(Widget):
    _button = Element('id::submit_button')
    _items = Element('xpath:://*[@class="item"]', multiple=True)
    _input = Element('id::email_input', mixin=MyMixin)
    _slow = Element('id::dynamic_element', polling=PollingConfig(timeout=15.0, delay=1.0))
```

**Constructor parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `locator` | `str` or `Locator` | required | Locator in `'strategy::value'` format |
| `multiple` | `bool` | `False` | Find multiple elements |
| `item` | `type[BasePage]` or `None` | `None` | Wrap each found `WebElement` into this page object class |
| `mixin` | `type[ElementMixin]` or `None` | `None` | Add custom methods to found `WebElement` |
| `polling` | `PollingConfig` or `None` | `None` | Override polling config (defaults to `PollingConfig()`) |

### Button / Input

Semantic aliases for `Element`. They behave identically but signal intent in page object declarations.

- `Button` — for clickable components (buttons, links, cards)
- `Input` — for text input components (text fields, text areas)

> In the current version, `Button` and `Input` do not add any methods of their own — they are placeholders for the future. When built-in `InputMixin` and `ButtonMixin` are introduced, the corresponding classes will automatically apply them upon element creation.

### Embedded

Descriptor that instantiates a nested page object (Widget or Item) on access. Enables multi-level composition.

```python
from composium import Embedded

class CheckoutScreen(Screen):
    payment = Embedded(PaymentWidget)
    receiver = Embedded(ReceiverWidget)
```

If the nested class has a `parent` set, e.g. `@define.widget(parent='id::root')`, the locator is resolved automatically — no need to pass `parent` to `Embedded`.

If you need to specify an additional search context (which element the search starts from), pass `payment = Embedded(PaymentWidget, parent='id::some_other_root')`

### CrossPlatformElement

Descriptor that selects the correct `Element` based on the active driver platform (Android or iOS).

**Three ways to declare a cross-platform element:**

1. **`from_id()`** — same locator value with native search strategies per platform:

   ```python
   name = CrossPlatformElement.from_id('card_name')
   # → android: Element('id::card_name'), ios: Element('accessibility-id::card_name')
   ```

   > ⚠️ `from_id()` does not support `multiple`, `item`, or `polling`. For these cases, use the full constructor.

2. **Full `CrossPlatformElement`** — different strategies/values + any `Element` parameters:

   ```python
   _items = CrossPlatformElement(
       android=Element('id::item_list', multiple=True, item=CardItem),
       ios=Element('name::item_list', multiple=True, item=CardItem),
   )
   ```

3. **Single `Element`** — when the element only needs a locator on one platform:

   ```python
   android_only = Element('id::android_specific')
   ```

---

## Locator Syntax

Locators use the `'strategy::value'` string format. If no `::` separator is found, strings starting with `/` default to `xpath`, otherwise to `id`.

**Supported strategies:**

| Strategy | Resolves to | Android searches by | iOS searches by | Example |
|---|---|---|---|---|
| `id::` | `By.ID` | `resource-id` | `name` attribute (legacy, NOT `accessibilityIdentifier`) | `'id::my_button'` |
| `accessibility-id::` | `AppiumBy.ACCESSIBILITY_ID` | `content-desc` | `accessibilityIdentifier` | `'accessibility-id::login'` |
| `name::` | `By.NAME` | — | `name` attribute (legacy) | `'name::search_field'` |
| `xpath::` | `By.XPATH` | DOM tree | DOM tree | `'xpath:://div[@class="x"]'` |
| `css::` | `By.CSS_SELECTOR` | CSS selector | — (not supported) | `'css::.my-class'` |
| `class::` | `By.CLASS_NAME` | class name | class name | `'class::android.widget.Button'` |

---

## Decorator DSL

```python
from composium.decorators import define
```
| Decorator | Applies to | Description |
|---|---|---|
| `@define.screen(name, deeplink=None)` | `Screen` subclass | `name` — screen name. `deeplink` — URL template for `ScreenFactory` navigation |
| `@define.widget(name, parent=None)` | `Widget` subclass | `name` — widget name. `parent` — root element locator, scopes child element lookup |
| `@define.item(name)` | `Item` subclass | `name` — item name |
| `@define.action(title)` | method | Wraps in `reporter.step('Action: {title}')` |
| `@define.assertion(title)` | method | Wraps in `reporter.step('Assert: {title}')` |
---

## ScreenFactory

Creates a screen and optionally navigates to it via deeplink.

```python
from composium import ScreenFactory

factory = ScreenFactory(driver)
home = factory(HomeScreen, account_id='ACC123')
```

If the screen has a `deeplink`, the factory interpolates the provided parameters into the template and calls `driver.get()`. If no `deeplink` is set — simply returns the screen without navigation.

---

## Reporter Integration

composium works without any reporting library. No reporter is connected by default.

### Enabling Allure

```python
import allure
import composium

composium.configure_reporter(composium.AllureReporter(allure))
```

### Custom Reporter

Implement the `ReporterProtocol` (duck typing):

```python
class MyReporter:
    def step(self, message: str): ...          # context manager
    def attach(self, body, *, name=None, attachment_type=None): ...
    def epic(self, *epics: str): ...
    def story(self, *stories: str): ...
    def feature(self, *features: str): ...

composium.configure_reporter(MyReporter())
```

> Note: `step()` must return a context manager (`@contextmanager` or a class with `__enter__`/`__exit__`).

---

## Utilities

### Cross-platform XPath

```python
from composium import xpath_contains_id

parent = xpath_contains_id('checkout_payment_root')
# → 'xpath::.//*[contains(@resource-id, "checkout_payment_root") or contains(@name, "checkout_payment_root")]'
```

Optional parameters:
- `prefix` (default `'.//*'`) — XPath prefix before the predicate
- `postfix` (default `''`) — suffix after the closing bracket

> Note: xpath on iOS is resource-intensive and slows down tests

### Platform Detection

```python
from composium import is_android, is_ios

if is_android(driver):
    # Android-specific logic
if is_ios(driver):
    # iOS-specific logic
```

Both functions read `driver.capabilities['platformName']`.
