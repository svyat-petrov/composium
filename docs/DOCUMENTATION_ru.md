# composium — Документация

Полный справочник по фреймворку composium.
Краткое введение — в [README.md](../README.md).

---

## Содержание

- [Основные концепции](#основные-концепции)
  - [LazyElement](#lazyelement)
  - [Polling](#polling)
  - [Диагностика падений](#диагностика-падений)
- [Иерархия Page Object](#иерархия-page-object)
  - [Screen](#screen)
  - [Widget](#widget)
  - [Item](#item)
- [Элементы страницы](#элементы-страницы)
  - [Element](#element)
  - [Button / Input](#button--input)
  - [Embedded](#embedded)
  - [CrossPlatformElement](#crossplatforment)
- [Синтаксис локаторов](#синтаксис-локаторов)
- [Декораторы DSL](#декораторы-dsl)
- [ScreenFactory](#screenfactory)
- [Интеграция с репортером](#интеграция-с-репортером)
- [Утилиты](#утилиты)

---

## Основные концепции

### LazyElement

`Element` — Python-дескриптор. При обращении на экземпляре page object создаёт прокси `LazyElement`. Реальный вызов `find_element` откладывается до момента использования:

```python
class MyWidget(Widget):
    button = Element('id::submit')  # find_element ещё не было

def test_something(my_widget):
    my_widget.button.click()  # find_element происходит здесь
```

**API LazyElement:**

| Метод / Свойство | Описание |
|---|---|
| `click()`, `text`, `get_attribute()`, ... | Пробрасываются к underlying `WebElement` через `__getattr__` |
| `__iter__` | Итерация по коллекции элементов (при `multiple=True`) |
| `__getitem__(index)` | Доступ к элементу по индексу из коллекции |
| `count` | Количество найденных элементов (0, 1 или длина списка) |
| `reload()` | Принудительный повторный поиск элемента |
| `exists()` | Проверка существования элемента без выброса исключения (возвращает `bool`) |
| `polling` | `PollingConfig` для данного элемента |

### Polling

Каждый поиск элемента включает автоматический retry при `NoSuchElementException`.

**По умолчанию:** `PollingConfig(timeout=10.0, delay=0.5)`

Переопределение на уровне элемента:

```python
from composium import Element, PollingConfig

_slow_element = Element(
    'xpath::.//*[contains(@text, "loading")]',
    polling=PollingConfig(timeout=15.0, delay=1.0),
)
```

> ⚠️ Глобальная конфигурация polling пока не реализована. Каждый элемент без явного параметра `polling` использует дефолтный `PollingConfig()`. Проектный override запланирован — см. Roadmap в README.

### Диагностика падений

Когда поиск элемента неуспешен после всех попыток polling, composium автоматически:
1. Делает скриншот (`driver.get_screenshot_as_png()`)
2. Получает page source (`driver.page_source`)
3. Аттачит оба файла без дополнительной настройки (если allure подключен)

---

## Иерархия Page Object

### Screen

Page object верхнего уровня, представляющий полный экран приложения. Его `parent` — всегда `WebDriver`.

```python
from composium import Screen, Embedded
from composium.decorators import define

@define.screen(name='Home', deeplink='myapp://home?account_id={account_id}')
class HomeScreen(Screen):
    accounts = Embedded(AccountsWidget)
```

**ScreenMeta** (устанавливается через `@define.screen`):
- `name` — имя экрана
- `deeplink` — опциональный URL-шаблон для навигации через `ScreenFactory`

### Widget

Логический UI-блок с собственным корневым элементом. Поиск дочерних элементов ограничен этим корнем, а не всем экраном.

```python
from composium import Widget, Element, xpath_contains_id
from composium.decorators import define

@define.widget(name='Payment', parent=xpath_contains_id('payment_root'))
class PaymentWidget(Widget):
    _title = Element('id::payment_title')
    _methods = Element('xpath:://*[@class="method"]', multiple=True, item=PaymentMethodItem)
```

**WidgetMeta** (устанавливается через `@define.widget`):
- `name` — имя виджета
- `parent` — локатор корневого элемента. Если задан, поиск дочерних элементов ограничен этим корнем. Если None — поиск идёт от драйвера экрана.

### Item

Представляет один повторяющийся элемент в списке/коллекции. Используется с `Element(multiple=True, item=MyItem)`.

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

**ItemMeta** (устанавливается через `@define.item`):
- `name` — имя айтема (повторяющегося элемента)

`Item` наследуется от `BasePage` и предоставляет `is_displayed()`, который делегирует вызов `WebElement.is_displayed()` родительского элемента.

## Элементы страницы

### Element

Python-дескриптор, создающий `LazyElement` при обращении на экземпляре page object.

```python
from composium import Element, PollingConfig

class MyWidget(Widget):
    _button = Element('id::submit_button')
    _items = Element('xpath:://*[@class="item"]', multiple=True)
    _input = Element('id::email_input', mixin=MyMixin)
    _slow = Element('id::dynamic_element', polling=PollingConfig(timeout=15.0, delay=1.0))
```

**Параметры конструктора:**

| Параметр | Тип | По умолчанию | Описание                                                        |
|---|---|---|-----------------------------------------------------------------|
| `locator` | `str` или `Locator` | обязателен | Локатор в формате `'strategy::value'`                           |
| `multiple` | `bool` | `False` | Искать несколько элементов                                      |
| `item` | `type[BasePage]` или `None` | `None` | Обернуть каждый найденный `WebElement` в этот класс page object |
| `mixin` | `type[ElementMixin]` или `None` | `None` | Добавить пользовательские методы в найденный `WebElement`       |
| `polling` | `PollingConfig` или `None` | `None` | Переопределить polling-конфиг (по умолчанию `PollingConfig()`)  |

### Button / Input

Семантические алиасы для `Element`. Поведение полностью идентично — но сигнализируют о назначении в объявлениях page object.

- `Button` — для кликабельных компонентов (кнопки, ссылки, карточки)
- `Input` — для текстовых полей ввода

> В текущей версии `Button` и `Input` не добавляют собственных методов — это задел на будущее. Когда появятся встроенные `InputMixin` и `ButtonMixin`, классы будут автоматически применять их при создании элемента.

### Embedded

Дескриптор, создающий экземпляр вложенного page object (Widget или Item) при обращении. Обеспечивает многоуровневую композицию.

```python
from composium import Embedded

class CheckoutScreen(Screen):
    payment = Embedded(PaymentWidget)
    receiver = Embedded(ReceiverWidget)
```

Если у вложенного класса задан `parent`, например, `@define.widget(parent='id::root')`, то локатор резолвится автоматически — передавать `parent` в `Embedded` не нужно.

Если нужно задать дополнительный контекст поиска, от какого элемента будет начинаться поиск, то стоит передать `payment = Embedded(PaymentWidget, parent='id::some_other_root')`

### CrossPlatformElement

Дескриптор, выбирающий нужный `Element` в зависимости от платформы драйвера (Android или iOS).

**Три способа объявления кроссплатформенного элемента:**

1. **`from_id()`** — одинаковое значение локатора (нативные стратегии поиска для платформ):

   ```python
   name = CrossPlatformElement.from_id('card_name')
   # → android: Element('id::card_name'), ios: Element('accessibility-id::card_name')
   ```

   > ⚠️ `from_id()` не поддерживает `multiple`, `item` и `polling`. Для этих случаев используйте полный конструктор.

2. **Полный `CrossPlatformElement`** — разные стратегии/значения + любые параметры `Element`:

   ```python
   _items = CrossPlatformElement(
       android=Element('id::item_list', multiple=True, item=CardItem),
       ios=Element('name::item_list', multiple=True, item=CardItem),
   )
   ```

3. **Одиночный `Element`** — когда элемент нужен только на одной платформе:

   ```python
   android_only = Element('id::android_specific')
   ```

---

## Синтаксис локаторов

Локаторы используют строковый формат `'strategy::value'`. Если разделитель `::` не найден, строка, начинающаяся с `/`, по умолчанию резолвится в `xpath`, иначе в `id`.

**Поддерживаемые стратегии:**

| Стратегия | Разрешается в | Android ищет по | iOS ищет по | Пример |
|---|---|---|---|---|
| `id::` | `By.ID` | `resource-id` | атрибут `name` (legacy, НЕ `accessibilityIdentifier`) | `'id::my_button'` |
| `accessibility-id::` | `AppiumBy.ACCESSIBILITY_ID` | `content-desc` | `accessibilityIdentifier` | `'accessibility-id::login'` |
| `name::` | `By.NAME` | — | атрибут `name` (legacy) | `'name::search_field'` |
| `xpath::` | `By.XPATH` | DOM-дерево | DOM-дерево | `'xpath:://div[@class="x"]'` |
| `css::` | `By.CSS_SELECTOR` | CSS-селектор | — (не поддерживается) | `'css::.my-class'` |
| `class::` | `By.CLASS_NAME` | имя класса | имя класса | `'class::android.widget.Button'` |

---

## Декораторы DSL

```python
from composium.decorators import define
```
| Декоратор | Применяется к | Описание |
|---|---|---|
| `@define.screen(name, deeplink=None)` | subclass `Screen` | `name` — имя экрана. `deeplink` — шаблон URL для навигации через `ScreenFactory` |
| `@define.widget(name, parent=None)` | subclass `Widget` | `name` — имя виджета. `parent` — локатор корневого элемента, ограничивает поиск дочерних элементов |
| `@define.item(name)` | subclass `Item` | `name` — имя айтема |
| `@define.action(title)` | метод | Оборачивает в `reporter.step('Action: {title}')` |
| `@define.assertion(title)` | метод | Оборачивает в `reporter.step('Assert: {title}')` |
---

## ScreenFactory

Создаёт экран и опционально открывает его через deeplink.

```python
from composium import ScreenFactory

factory = ScreenFactory(driver)
home = factory(HomeScreen, account_id='ACC123')
```

Если у экрана задан `deeplink`, фабрика подставляет переданные параметры в шаблон и вызывает `driver.get()`. Если `deeplink` нет — просто возвращает экран без навигации.

---

## Интеграция с репортером

composium работает без библиотеки отчётности. По умолчанию репортер не подключён

### Подключение Allure

```python
import allure
import composium

composium.configure_reporter(composium.AllureReporter(allure))
```

### Кастомный репортер

Реализуйте `ReporterProtocol` (duck typing):

```python
class MyReporter:
    def step(self, message: str): ...          # context manager
    def attach(self, body, *, name=None, attachment_type=None): ...
    def epic(self, *epics: str): ...
    def story(self, *stories: str): ...
    def feature(self, *features: str): ...

composium.configure_reporter(MyReporter())
```

> Примечание: `step()` должен возвращать context manager (`@contextmanager` или класс с `__enter__`/`__exit__`).

---

## Утилиты

### Кроссплатформенный XPath

```python
from composium import xpath_contains_id

parent = xpath_contains_id('checkout_payment_root')
# → 'xpath::.//*[contains(@resource-id, "checkout_payment_root") or contains(@name, "checkout_payment_root")]'
```

Опциональные параметры:
- `prefix` (по умолчанию `'.//*'`) — XPath-префикс перед предикатом
- `postfix` (по умолчанию `''`) — суффикс после закрывающей скобки

> Примечание: xpath на iOS ресурсозатратен и замедляет тесты

### Определение платформы

```python
from composium import is_android, is_ios

if is_android(driver):
    # Логика для Android
if is_ios(driver):
    # Логика для iOS
```

Обе функции читают `driver.capabilities['platformName']`.
