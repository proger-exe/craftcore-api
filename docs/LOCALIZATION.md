# Документация по локализации

## Обзор

Система локализации позволяет хранить и управлять текстовыми сообщениями и кнопками для различных языков. Локализация реализована с использованием моделей Tortoise ORM и PostgreSQL.

## Модели

### Message

Модель для хранения текстовых сообщений с поддержкой множественных языков.

**Поля:**
- `message_id` (str, unique, max_length=4028) - Уникальный идентификатор сообщения
- `message_name` (str, nullable) - Название сообщения (опционально)
- `message_text` (str) - Основной текст сообщения (язык по умолчанию)
- `message_text_another_langs` (JSON) - Словарь с переводами на другие языки

**Пример использования:**
```python
from models.localization.locale import Message, Languages

# Создание сообщения
message = await Message.create(
    message_id="user-welcome-hello",
    message_name="Приветствие пользователя",
    message_text="Добро пожаловать!",
    message_text_another_langs={
        "en": "Welcome!",
        "ru": "Добро пожаловать!"
    }
)

# Получение сообщения на нужном языке
def get_message_text(message: Message, lang: Languages) -> str:
    if lang.value in message.message_text_another_langs:
        return message.message_text_another_langs[lang.value]
    return message.message_text  # Возвращаем текст по умолчанию
```

### Button

Модель для хранения текстов кнопок с привязкой к языку.

**Поля:**
- `button_id` (str, max_length=4028) - Идентификатор кнопки
- `button_text` (str) - Текст кнопки
- `lang` (Languages enum) - Язык кнопки

**Пример использования:**
```python
from models.localization.locale import Button, Languages

# Создание кнопок для разных языков
button_ru = await Button.create(
    button_id="user-menu-shop",
    button_text="Магазин",
    lang=Languages.RU
)

button_en = await Button.create(
    button_id="user-menu-shop",
    button_text="Shop",
    lang=Languages.EN
)

# Получение текста кнопки по ID и языку
async def get_button_text(button_id: str, lang: Languages) -> str:
    button = await Button.filter(button_id=button_id, lang=lang).first()
    return button.button_text if button else button_id
```

### Languages

Enum для поддерживаемых языков.

**Доступные языки:**
- `Languages.RU` - Русский
- `Languages.EN` - Английский

**Пример использования:**
```python
from models.localization.locale import Languages

# Получение кода языка
lang_code = Languages.RU.value  # "ru"
lang_code = Languages.EN.value  # "en"
```

## Стандарт именования (Namespace)

Для создания локализации нужно соблюдать следующий формат:

### Формат

`{type}-{module}-{uid}`

- **type** - Тип локализации (system, admin, user)
- **module** - Название модуля (например: `nicksearch`, `ecofix`). Не содержит `-` или другие уникоды
- **uid** - Уникальное обозначение текста. Не обязан быть солидным

### Типы

- `system` - Системные сообщения
- `admin` - Сообщения для администраторов
- `user` - Сообщения для пользователей

### Примеры

- `admin-userseach-not-found` - Сообщение об ошибке "не найдено" в админке при поиске пользователя
- `user-welcome-hello` - Приветственное сообщение для пользователя
- `system-error-database` - Системное сообщение об ошибке базы данных
- `user-menu-shop` - Кнопка меню "Магазин" для пользователя

## Работа с базой данных

### Инициализация

База данных инициализируется автоматически при запуске приложения через функцию `models.init()`:

```python
from models import init

# В main.py или при старте приложения
await init()
```

### Создание записей

```python
from models.localization.locale import Message, Button, Languages

# Создание сообщения
message = await Message.create(
    message_id="user-welcome-hello",
    message_text="Добро пожаловать!",
    message_text_another_langs={"en": "Welcome!"}
)

# Создание кнопки
button = await Button.create(
    button_id="user-menu-shop",
    button_text="Магазин",
    lang=Languages.RU
)
```

### Получение записей

```python
# Получить сообщение по ID
message = await Message.get(message_id="user-welcome-hello")

# Получить все кнопки с определенным ID
buttons = await Button.filter(button_id="user-menu-shop").all()

# Получить кнопку по ID и языку
button = await Button.filter(
    button_id="user-menu-shop",
    lang=Languages.RU
).first()
```

### Обновление записей

```python
# Обновить текст сообщения
message = await Message.get(message_id="user-welcome-hello")
message.message_text = "Новый текст"
await message.save()

# Обновить переводы
message.message_text_another_langs["en"] = "New Welcome Text"
await message.save()
```

### Удаление записей

```python
# Удалить сообщение
message = await Message.get(message_id="user-welcome-hello")
await message.delete()

# Удалить кнопку
button = await Button.filter(button_id="user-menu-shop", lang=Languages.RU).first()
if button:
    await button.delete()
```

## Рекомендации

1. **Используйте осмысленные message_id** - это упростит поиск и поддержку кода
2. **Храните основной текст на языке по умолчанию** - это гарантирует, что всегда будет доступен хотя бы один вариант текста
3. **Используйте message_name для описания** - это поможет другим разработчикам понять назначение сообщения
4. **Следуйте стандарту именования** - это обеспечит консистентность в проекте
5. **Группируйте кнопки по button_id** - используйте один button_id для всех языков одной кнопки

## Интеграция с Player

Модель `Player` содержит поле `language`, которое определяет предпочитаемый язык пользователя:

```python
from models.players.players import Player
from models.localization.locale import Languages

# Получить язык пользователя
player = await Player.get(tg_id=123456789)
user_lang = player.language  # Languages.RU или Languages.EN

# Использовать язык пользователя для получения локализованного текста
message = await Message.get(message_id="user-welcome-hello")
if user_lang.value in message.message_text_another_langs:
    text = message.message_text_another_langs[user_lang.value]
else:
    text = message.message_text
```

## Миграции

При первом запуске приложения схема базы данных создается автоматически. Для обновления схемы используйте:

```python
from tortoise import Tortoise

# Генерация схемы (безопасно - не перезаписывает существующие таблицы)
await Tortoise.generate_schemas(safe=True)
```

## Закрытие соединений

При завершении работы приложения необходимо закрыть соединения с базой данных:

```python
from models import close

# При завершении приложения
await close()
```

