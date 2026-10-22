# Система ареста (Arrest)

## Обзор

Система ареста позволяет администраторам временно ограничивать игроков с обязательным сроком заключения. В отличие от банов, арест всегда имеет срок окончания, но может быть досрочно снят администратором.

## Отличия от других систем модерации

- **Ban (Бан)**: Может быть бессрочным или с опциональным сроком. Полное исключение из системы.
- **Mute (Мут)**: Обязательный срок, но нет возможности досрочного снятия. Ограничение только на чат.
- **Arrest (Арест)**: Обязательный срок, но есть возможность досрочного освобождения. Временное ограничение игрока.

## Модель данных

### Arrest

Модель ареста содержит следующую информацию:

- `id` (`BigInt`) - уникальный идентификатор ареста
- `player` (`models.Player`) - арестованный игрок (ForeignKey, CASCADE)
- `admin` (`models.Player`, optional) - администратор, который вынес арест (null для системных арестов)
- `reason` (`str`) - причина ареста
- `arrested_at` (`Datetime`) - время ареста (автоматически устанавливается при создании)
- `expires_at` (`Datetime`) - срок окончания ареста (обязательное поле)
- `is_active` (`bool`) - активен ли арест (по умолчанию `True`)
- `released_at` (`Datetime`, optional) - время досрочного освобождения
- `released_by` (`models.Player`, optional) - администратор, который освободил игрока

### Индексы

Таблица `arrests` имеет индексы на:
- `player` - для быстрого поиска арестов игрока
- `is_active` - для фильтрации активных арестов
- `expires_at` - для проверки истечения сроков

## API Эндпоинты

Все эндпоинты требуют аутентификации с ролью `ADMIN` или `OWNER` (через `get_current_admin`).

### Создание ареста

Создать новый арест для игрока.

```http
POST /admin/arrests
```

**Тело запроса:**

```json
{
  "player_id": 123,
  "reason": "Violation of server rules",
  "expires_at": "2024-12-31T23:59:59"
}
```

**Поля:**
- `player_id` (int, required) - ID игрока
- `reason` (string, required) - причина ареста
- `expires_at` (datetime, required) - срок окончания ареста (ISO 8601 формат)

**Ответы:**
- `201` - Арест успешно создан (Схема: `ArrestResponse`)
- `404` - Игрок не найден
- `422` - Ошибка валидации
- `500` - Внутренняя ошибка сервера

**Пример ответа:**

```json
{
  "id": 1,
  "player_id": 123,
  "admin_id": 456,
  "reason": "Violation of server rules",
  "arrested_at": "2024-01-15T10:30:00",
  "expires_at": "2024-12-31T23:59:59",
  "is_active": true,
  "released_at": null,
  "released_by_id": null
}
```

---

### Получение ареста по ID

Получить информацию об аресте по его ID.

```http
GET /admin/arrests/{arrest_id}
```

**Параметры:**
- `arrest_id` (integer, required) - ID ареста

**Ответы:**
- `200` - Успешный ответ (Схема: `ArrestResponse`)
- `404` - Арест не найден

---

### Получение всех арестов игрока

Получить список всех арестов конкретного игрока.

```http
GET /admin/arrests/player/{player_id}
```

**Параметры:**
- `player_id` (integer, required) - ID игрока
- `active_only` (boolean, optional, default: `false`) - возвращать только активные аресты

**Ответы:**
- `200` - Успешный ответ (Массив: `ArrestResponse`)
- `404` - Игрок не найден

**Пример запроса:**

```http
GET /admin/arrests/player/123?active_only=true
```

---

### Проверка активного ареста

Проверить, есть ли у игрока активный арест.

```http
GET /admin/arrests/player/{player_id}/check
```

**Параметры:**
- `player_id` (integer, required) - ID игрока

**Ответы:**
- `200` - Успешный ответ
- `404` - Игрок не найден

**Пример ответа:**

```json
{
  "is_arrested": true,
  "arrest": {
    "id": 1,
    "player_id": 123,
    "admin_id": 456,
    "reason": "Violation of server rules",
    "arrested_at": "2024-01-15T10:30:00",
    "expires_at": "2024-12-31T23:59:59",
    "is_active": true,
    "released_at": null,
    "released_by_id": null
  }
}
```

Если игрок не арестован:

```json
{
  "is_arrested": false,
  "arrest": null
}
```

---

### Досрочное освобождение

Освободить игрока из ареста до истечения срока.

```http
POST /admin/arrests/{arrest_id}/release
```

**Параметры:**
- `arrest_id` (integer, required) - ID ареста

**Ответы:**
- `200` - Игрок успешно освобожден (Схема: `ArrestResponse`)
- `404` - Арест не найден
- `500` - Внутренняя ошибка сервера

**Пример ответа:**

```json
{
  "id": 1,
  "player_id": 123,
  "admin_id": 456,
  "reason": "Violation of server rules",
  "arrested_at": "2024-01-15T10:30:00",
  "expires_at": "2024-12-31T23:59:59",
  "is_active": false,
  "released_at": "2024-01-20T15:00:00",
  "released_by_id": 789
}
```

---

### Удаление ареста

Удалить запись об аресте из базы данных.

```http
DELETE /admin/arrests/{arrest_id}
```

**Параметры:**
- `arrest_id` (integer, required) - ID ареста

**Ответы:**
- `200` - Арест успешно удален
- `404` - Арест не найден

**Пример ответа:**

```json
{
  "message": "Arrest deleted successfully"
}
```

---

## Логирование действий

Все действия с арестами автоматически логируются в `AdminActionLog`:

- **Создание ареста**: `action_type = "arrest"`, детали содержат `reason` и `expires_at`
- **Освобождение**: `action_type = "release"`, детали содержат `arrest_id`

## Проверка активного ареста

Арест считается активным, если:
- `is_active = True`
- `expires_at > текущее время`

Арест автоматически становится неактивным после истечения срока (`expires_at`), но это не происходит автоматически - проверка выполняется при каждом запросе.

## Примеры использования

### Пример 1: Арест игрока на 7 дней

```bash
curl -X POST "https://api.example.com/admin/arrests" \
  -H "X-Player-ID: 456" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": 123,
    "reason": "Griefing other players",
    "expires_at": "2024-01-22T10:30:00"
  }'
```

### Пример 2: Проверка активного ареста

```bash
curl -X GET "https://api.example.com/admin/arrests/player/123/check" \
  -H "X-Player-ID: 456"
```

### Пример 3: Досрочное освобождение

```bash
curl -X POST "https://api.example.com/admin/arrests/1/release" \
  -H "X-Player-ID: 456"
```

### Пример 4: Получение всех арестов игрока

```bash
curl -X GET "https://api.example.com/admin/arrests/player/123?active_only=true" \
  -H "X-Player-ID: 456"
```

## Схемы данных

### ArrestCreate

Схема для создания ареста:

```python
{
    "player_id": int,
    "reason": str,
    "expires_at": datetime  # ISO 8601 format
}
```

### ArrestResponse

Схема ответа с информацией об аресте:

```python
{
    "id": int,
    "player_id": int,
    "admin_id": int | None,
    "reason": str,
    "arrested_at": datetime,
    "expires_at": datetime,
    "is_active": bool,
    "released_at": datetime | None,
    "released_by_id": int | None
}
```

## Примечания

1. **Обязательный срок**: В отличие от банов, арест всегда должен иметь срок окончания (`expires_at` обязателен).

2. **Досрочное освобождение**: Арест может быть снят досрочно администратором через эндпоинт `/release`. При этом устанавливаются поля `is_active=False`, `released_at=now()`, `released_by=admin`.

3. **Автоматическое истечение**: Арест не становится неактивным автоматически при истечении срока. Проверка выполняется при каждом запросе через условие `expires_at > now()`.

4. **Логирование**: Все действия логируются в `AdminActionLog` для аудита.

5. **CASCADE удаление**: При удалении игрока все его аресты удаляются автоматически (CASCADE).
