# composium

Declarative multi-layered Page Object framework for cross-platform mobile test automation (Android + iOS). Built on Appium.

## Why composium?

Mobile UI tests are flaky. Standard Page Objects mix logic and element definitions, producing non-reusable code. Cross-platform locators are scattered across files.

**composium** solves this through a declarative, composable architecture:

- **Declarative** — elements are Python descriptors, no manual `find_element`
- **Multi-layered** — Screen → Widget → Item → Element, each scoped to its DOM subtree
- **Cross-platform** — one element definition, automatic Android/iOS locator selection
- **Polling out of the box** — configurable retry on `NoSuchElementException`, no explicit/implicit waits
- **Failure diagnostics** — screenshot + page_source attached automatically on lookup failure
- **Optional Allure** — reporter abstraction, works without any reporting library

## Installation

```bash
pip install git+https://github.com/svyat-petrov/composium.git
```

With Allure integration:

```bash
pip install git+https://github.com/svyat-petrov/composium.git allure-python-commons
```

Requires Python 3.12+.

## Quick Start

```python
from composium import Screen, Widget, Item, Element, Embedded, CrossPlatformElement, PollingConfig, xpath_contains_id
from composium import ScreenFactory
from composium.decorators import define


@define.screen(name='Home', deeplink='myapp://home?account_id={account_id}')
class HomeScreen(Screen):
    accounts = Embedded(AccountsWidget)


@define.widget(name='Accounts', parent=xpath_contains_id('accounts_section'))
class AccountsWidget(Widget):
    _accounts = CrossPlatformElement(
        android=Element('id::account_list', multiple=True, item=CardItem),
        ios=Element('name::account_list', multiple=True, item=CardItem),
    )

    @define.action('get account by name')
    def get_account(self, name: str) -> CardItem:
        for card in self._accounts:
            if card.name.text == name:
                return card
        raise AssertionError(f'Account "{name}" not found')


@define.item('Card')
class CardItem(Item):
    name = CrossPlatformElement.from_id('card_name')
    _select = CrossPlatformElement.from_id('radio_button')

    @define.action('select card')
    def select(self) -> None:
        self._select.click()


def test_account_selection(driver):
    factory = ScreenFactory(driver)
    home = factory(HomeScreen, account_id='ACC123')
    card = home.accounts.get_account('Main')
    card.select()
```

## Architecture

Each level dynamically resolves its parent:

```
Screen          — full app screen, parent = WebDriver
 └── Widget     — UI block, parent = root WebElement
      └── Item  — repeated list element, parent = single WebElement
           └── Element — leaf descriptor, creates LazyElement on access
```

## Documentation | Документация

- 🇬🇧 [Documentation](docs/DOCUMENTATION.md)
- 🇷🇺 [Документация](docs/DOCUMENTATION_ru.md)

## Roadmap

- **Global polling config** — project-wide `PollingConfig` override (currently only per-element). 
- **Screenshot testing** — visual regression via pixel/diff comparison. Feasibility: medium complexity — requires image diff library (e.g. `pixelmatch`), baseline storage strategy, and Appium screenshot stability handling. Not trivial but doable.
- **ElementMixin extensions** — built-in `InputMixin` (clear + type shortcuts), `ScrollMixin` (scroll-to-element) and `ButtonMixin` for button and hyperlinks. `ElementMixin` base class already exists, injection via `__class__` reassignment is implemented.
- **CrossPlatformElement.from_id()** – support the parameters that the Element has
- **Meta name in reports** — propagate `Screen`/`Widget`/`Item` `meta.name` into reporter steps (e.g., `Action: [Payment] select method`)

## License

MIT