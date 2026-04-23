# composium

Декларативный многоуровневый Page Object фреймворк для кроссплатформенной мобильной автоматизации (Android + iOS). Построен на Appium.

## Зачем composium?

Мобильные UI-тесты нестабильны. Стандартный Page Objects — смешивает логику и описание элементов, 
добавляя непереиспользуемый код. Кроссплатформенные локаторы — разрозненны.

**composium** решает это через декларативную, компонуемую архитектуру:

- **Декларативность** — элементы описываются как дескрипторы, без ручных `find_element`
- **Многоуровневость** — Screen → Widget → Item → Element, каждый scoped к своему DOM-поддереву
- **Кроссплатформенность** — одно определение элемента, автоматический выбор Android/iOS локатора
- **Polling из коробки** — настраиваемый retry при `NoSuchElementException`, без явных/неявных waits
- **Диагностика падений** — скриншот + page_source аттачатся автоматически при ошибке поиска элемента
- **Опциональный Allure** — абстракция репортера, можно работать и без библиотеки отчетности

## Установка

```bash
pip install composium
```

С интеграцией Allure:

```bash
pip install composium[allure]
```

Требуется Python 3.12+.

## Быстрый старт

### 1. Определи Screen

```python
from composium import Screen, Embedded
from composium.decorators import define


@define.screen(name='Home', deeplink='myapp://home?account_id={account_id}')
class HomeScreen(Screen):
    accounts = Embedded(AccountsWidget)
```

### 2. Определи Widget

```python
from composium import Widget, Element, CrossPlatformElement, xpath_contains_id
from composium.decorators import define


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
```

### 3. Определи Item

```python
from composium import Item, Element, CrossPlatformElement, PollingConfig
from composium.decorators import define


@define.item('Card')
class CardItem(Item):
    # Одинаковое значение, поиск по: id (Android) / accessibility-id (iOS)
    name = CrossPlatformElement.from_id('card_name')

    # Разные стратегии на каждой платформе
    currency = CrossPlatformElement(
        android=Element('id::card_currency'),
        ios=Element('name::card_currency'),
    )

    _select = CrossPlatformElement.from_id('radio_button')

    # Кроссплатформенный элемент с кастомным polling
    _balance = CrossPlatformElement(
        android=Element(
            'xpath::.//*[contains(@text, "balance_value")]',
            polling=PollingConfig(timeout=15.0, delay=1.0),
        ),
        ios=Element(
            'xpath::.//*[contains(@label, "balance_value")]',
            polling=PollingConfig(timeout=15.0, delay=1.0),
        ),
    )

    @define.action('select card')
    def select(self) -> None:
        self._select.click()

    @define.assertion('card is selected')
    def is_selected(self) -> bool:
        return self._select.get_attribute('enabled') == 'true'

    @define.assertion('balance is positive')
    def balance_is_positive(self) -> bool:
        return float(self._balance.text) > 0
```

### 4. Используй в тестах

```python
from composium import ScreenFactory


def test_account_selection(driver):
    factory = ScreenFactory(driver)

    home = factory(HomeScreen, account_id='ACC123')
    accounts = home.accounts

    card = accounts.get_account('Main').select()
    card.is_selected()
    card.balance_is_positive()
```

## Архитектура
Каждый уровень динамически резолвит свой parent
```
Screen          — полный экран приложения, parent = WebDriver
 └── Widget     — UI-блок, parent = корневой WebElement
      └── Item  — повторяющийся элемент списка, parent = одиночный WebElement
           └── Element — листовой дескриптор, создаёт LazyElement при обращении
```

## Основные концепции

### LazyElement

`Element` — дескриптор, который при обращении создаёт прокси `LazyElement`. Реальный `find_element` откладывается до момента использования:

```python
class MyWidget(Widget):
    button = Element('id::submit')  # find_element ещё не было

def test_something(my_widget):
    my_widget.button.click()  # find_element происходит здесь
```
### Polling
Каждый элемент ищется с retry по умолчанию: `PollingConfig(timeout=10.0, delay=0.5)`.  
Можно переопределить на уровне элемента: `Element('id::x', polling=PollingConfig(timeout=15.0, delay=1.0))`.  
Можно определить на весь проект через конфиг


```python
from composium import PollingConfig

_some_element = CrossPlatformElement(
    android=Element(
        'id::some_element',
        polling=PollingConfig(timeout=15.0, delay=1.0),
    ),
    ios=Element(
        'name::some_element',
        polling=PollingConfig(timeout=15.0, delay=1.0),
    ),
)
```
## Синтаксис локаторов

**Appium-стратегии поиска по платформам:**

| Стратегия (strategy::) | Разрешается в               | Android ищет по | iOS ищет по                                 | Пример `strategy::value`     |
|------------------------|-----------------------------|-----------------|---------------------------------------------|------------------------------|
| `id::`                 | `By.ID`                     | `resource-id`   | `name` (legacy, НЕ accessibilityIdentifier) | `'id::my_button'`            |
| `accessibility-id::`   | `AppiumBy.ACCESSIBILITY_ID` | —               | `accessibilityIdentifier`                   | `'accessibility-id::login'`  |
| `name::`               | `By.NAME`                   | —               | `name` (legacy)                             |                              |
| `xpath::`              | `By.XPATH`                  | DOM-дерево      | DOM-дерево                                  | `'xpath:://div[@class="x"]'` |
| `css::`                | `By.CSS_SELECTOR`           | CSS-селектор    | — (не поддерживается)                       |                              |
| `class::`              | `By.CLASS_NAME`             | имя класса      | имя класса                                  |                              |

**3 варианта объявления кроссплатформенного элемента:**

1. **`from_id()`** — одинаковое значение
   ```python
   name = CrossPlatformElement.from_id('card_name')
   # → android: Element('id::card_name'), ios: Element('accessibility-id::card_name')
   ```

2. **Полный `CrossPlatformElement`** — разные стратегии и/или значения + любые параметры Element:
   ```python
   _some_elements = CrossPlatformElement(
       android=Element('id::some_id', multiple=True, item=CardItem, polling=PollingConfig(timeout=15.0, delay=1.0)),
       ios=Element('name::some_name', multiple=True, item=CardItem, polling=PollingConfig(timeout=15.0, delay=1.0)),
   )
   ```

3. **Одиночный `Element`** — когда элемент нужно описать только на одной платформе
   ```python
   android_only = Element('id::android_specific')
   ```

## Утилиты


### Интеграция с репортером

composium работает без библиотек отчётности. Чтобы включить Allure:

```python
import allure
import composium

composium.configure_reporter(composium.AllureReporter(allure))
```

Кастомный репортер — реализуй протокол (duck typing):

```python
class MyReporter:
    def step(self, message): ...
    def attach(self, body, *, name=None, attachment_type=None): ...
    def epic(self, *epics): ...
    def story(self, *stories): ...
    def feature(self, *features): ...

composium.configure_reporter(MyReporter())
```
### Кросс-платформенный xpath
`xpath_contains_id('x')` — кроссплатформенный xpath: `xpath::.//*[contains(@resource-id, "x") or contains(@name, "x")]`
### Определение платформы
- `is_android(driver)` / `is_ios(driver)` — проверка платформы по `driver.capabilities['platformName']`

### Диагностика падений

Когда поиск элемента неуспешен после всех попыток polling, composium автоматически аттачит скриншот и page source в репортер. Без дополнительной конфигурации.

### DSL декораторов

```python
from composium.decorators import define

@define.screen(name='Home', deeplink='myapp://home')
class HomeScreen(Screen): ...

@define.widget(name='Accounts', parent=xpath_contains_id('accounts_section'))
class AccountsWidget(Widget): ...

@define.item('Card')
class CardItem(Item): ...

@define.action('select account')
def select_account(self, name): ...

@define.assertion('card is selected')
def is_selected(self): ...
```
## Лицензия

MIT
