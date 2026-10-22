# API Documentation

## Общая информация

API построен на FastAPI и предоставляет RESTful endpoints для управления игровым сервером.
Все endpoints требуют аутентификации через заголовок `X-Player-ID`.

**Base URL**: `https://api.example.com`

**OpenAPI Schema**: `https://api.example.com/openapi.json`

**Swagger UI**: `https://api.example.com/`

**ReDoc**: `https://api.example.com/redoc`

## Аутентификация

Все запросы требуют заголовок `X-Player-ID` с ID игрока:

```
X-Player-ID: 123
```

Для больших ID можно передавать значение строкой (избегает потери точности в JSON number).

`X-Player-ID` сам по себе ничем не подписан — он говорит, от чьего имени выполняется запрос, но не подтверждает, какой сервис его прислал. Системный аккаунт (`id 777000`, см. `docs/DATABASE_MIGRATIONS.md`) — исключение: чтобы прислать `X-Player-ID: 777000`, запрос обязан нести ещё и заголовок `Authorization: Bearer <service_token>` с валидным сервисным JWT. Токен выдаётся доверенным бэкендам (бот, админ-панель) через:

```
POST /integrations/auth/token
{"client_id": "...", "client_secret": "..."}
```

Пара `client_id:client_secret` регистрируется в `.env` через `SERVICE_CREDENTIALS` (см. `settings.py`), токен живёт `JWT_SERVICE_TOKEN_TTL_MINUTES` минут (по умолчанию 60). Для всех остальных `player_id` поведение не изменилось — `X-Player-ID` работает как раньше.

### Роли доступа

- **Пользовательские endpoints** (`/user/...`) доступны любому авторизованному игроку (заголовок `X-Player-ID` с существующим игроком).

- **Админ-эндпоинты** различаются по требуемой роли:
  - **Admin/Owner** (`get_current_admin`): роль `ADMIN` или `OWNER`. Доступ к настройкам бота (`/admin/settings`), созданию голосований (`POST /admin/votes`), заморозке/разморозке кошелька (`/admin/wallet/...`), аресту/освобождению игроков (`/admin/arrests/...`), аналитике (server-snapshot, player sessions), статистике, объявлениям, уведомлениям, реферальной сводке (`GET /admin/referrals/stats`).
  - **Moderator** (`get_current_moderator`): роли `ADMIN`, `OWNER` или `MODERATOR`. Доступ к Identity, включая отвязку Telegram (`/admin/identity/...`), списку заявок на смену ника и approve/reject (`/admin/nickchange/...`).
  - **Support** (`get_current_support`): роли `ADMIN`, `OWNER`, `MODERATOR` или `SUPPORT`. Доступ к поиску игроков (`GET /admin/players/search`) и досье игрока (`GET /admin/analytics/player/{player_id}/dossier`).

Перечисление ролей (`PlayerRoles`): `GUEST`, `PLAYER`, `MODERATOR`, `SUPPORT`, `ADMIN`, `OWNER`.

## Коды ответов

- `200` - Успешный запрос
- `201` - Ресурс создан
- `400` - Неверный запрос
- `401` - Не авторизован
- `402` - Недостаточно средств (например, покупка в шопе, `POST /user/shops/{shop_id}/items/{item_id}/buy`)
- `403` - Доступ запрещен
- `404` - Ресурс не найден
- `409` - Конфликт (например, ресурс уже привязан к другому аккаунту)
- `422` - Ошибка валидации
- `500` - Внутренняя ошибка сервера

---

## ADMIN Endpoints

### Create Announcement Endpoint

Create a new announcement

```http
POST /admin/announcements
```

**Параметры:**


**Тело запроса:**

Схема: `AnnouncementCreate`

**Ответы:**

- `201` - Successful Response (Схема: `AnnouncementResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Announcement Endpoint

Delete an announcement

```http
DELETE /admin/announcements/{announcement_id}
```

**Параметры:**

- `announcement_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Announcement Endpoint

Update an announcement

```http
PUT /admin/announcements/{announcement_id}
```

**Параметры:**

- `announcement_id` (integer (required)) - No description

**Тело запроса:**

Схема: `AnnouncementUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `AnnouncementResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Ban

Create a ban for a player

```http
POST /admin/bans
```

**Параметры:**


**Тело запроса:**

Схема: `BanCreate`

**Ответы:**

- `201` - Successful Response (Схема: `BanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Bans By Player

Get all bans for a player

```http
GET /admin/bans/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `active_only` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `BanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Check Player Banned

Check if player is currently banned

```http
GET /admin/bans/player/{player_id}/check
```

**Параметры:**

- `player_id` (integer (required)) - Player ID

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Ban Endpoint

Delete a ban

```http
DELETE /admin/bans/{ban_id}
```

**Параметры:**

- `ban_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Ban By Id

Get ban by ID

```http
GET /admin/bans/{ban_id}
```

**Параметры:**

- `ban_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `BanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Unban Player Endpoint

Unban a player

```http
POST /admin/bans/{ban_id}/unban
```

**Параметры:**

- `ban_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `BanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Admin Logs Endpoint

Get admin action logs

```http
GET /admin/logs
```

**Параметры:**

- `admin_id` (string (optional)) - No description
- `action_type` (string (optional)) - No description
- `limit` (integer (optional)) - No description
- `offset` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `AdminActionLogResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Player Logs

Get admin logs for a specific player

```http
GET /admin/logs/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `limit` (integer (optional)) - No description
- `offset` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `AdminActionLogResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Mute

Create a mute for a player

```http
POST /admin/mutes
```

**Параметры:**


**Тело запроса:**

Схема: `MuteCreate`

**Ответы:**

- `201` - Successful Response (Схема: `MuteResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Mutes By Player

Get all mutes for a player

```http
GET /admin/mutes/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `active_only` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `MuteResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Check Player Muted

Check if player is currently muted

```http
GET /admin/mutes/player/{player_id}/check
```

**Параметры:**

- `player_id` (integer (required)) - Player ID

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Mute Endpoint

Delete a mute

```http
DELETE /admin/mutes/{mute_id}
```

**Параметры:**

- `mute_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Mute By Id

Get mute by ID

```http
GET /admin/mutes/{mute_id}
```

**Параметры:**

- `mute_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `MuteResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Unmute Player Endpoint

Unmute a player

```http
POST /admin/mutes/{mute_id}/unmute
```

**Параметры:**

- `mute_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `MuteResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Bulk Notification Endpoint

Send bulk notifications

```http
POST /admin/notifications/bulk
```

**Параметры:**


**Тело запроса:**

Схема: `NotificationBulkCreate`

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Send Notification To Role Endpoint

Send notification to all players with specific role

```http
POST /admin/notifications/role
```

**Параметры:**

- `role` (string (required)) - No description
- `title` (string (required)) - No description
- `content` (string (required)) - No description
- `notification_type` (string (optional)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Economy Statistics Endpoint

Get economy statistics for a date range

```http
GET /admin/statistics/economy
```

**Параметры:**

- `start_date` (string (optional)) - No description
- `end_date` (string (optional)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Player Statistics Endpoint

Get comprehensive statistics for a player

```http
GET /admin/statistics/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Server Statistics Endpoint

Get server-wide statistics

```http
GET /admin/statistics/server
```

**Параметры:**


**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Playtime Rewards Push Endpoint

Создать записи в очереди наград для игроков, отыгравших 2+ часа. Вызывается сервером/метриками.

```http
POST /admin/playtime-rewards
```

**Тело запроса:** Схема: `PlaytimeRewardBatch` — объект с полем `players`, где каждый элемент:

- `player_id` — ID игрока;
- `playtime_seconds` — количество секунд игрового времени (обычно ≥ 7200 для 2+ часов).

**Ответы:**

- `200` — `{ "inserted": N }`, где `N` — число добавленных записей;
- `401`, `403`, `500`.

---

### Playtime Rewards Pop Endpoint

Забрать все ожидающие записи очереди наград и сразу же удалить их (pop-поведение). Вызывается ботом.

```http
GET /admin/playtime-rewards/pending
```

**Ответы:**

- `200` — массив объектов `PlaytimeRewardRecord`:
  - `id` — ID записи в очереди;
  - `player_id` — ID игрока;
  - `playtime_seconds` — отыгранное время в секундах;
  - `created_at` — время добавления записи в очередь.
- `401`, `403`, `500`.

### Create Warn

Create a warn for a player

```http
POST /admin/warns
```

**Параметры:**


**Тело запроса:**

Схема: `WarnCreate`

**Ответы:**

- `201` - Successful Response (Схема: `WarnResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Warns By Player

Get all warns for a player

```http
GET /admin/warns/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `active_only` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `WarnResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Warn Endpoint

Delete a warn

```http
DELETE /admin/warns/{warn_id}
```

**Параметры:**

- `warn_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Warn By Id

Get warn by ID

```http
GET /admin/warns/{warn_id}
```

**Параметры:**

- `warn_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `WarnResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Arrest (Admin)

Создать арест для игрока. В отличие от бана/мута, у ареста всегда обязателен срок окончания (`expires_at`); он может быть снят досрочно. Подробнее см. [docs/ARRESTS.md](docs/ARRESTS.md).

```http
POST /admin/arrests
```

**Тело запроса:**

Схема: `ArrestCreate` (player_id, reason, expires_at)

**Ответы:**

- `201` - Successful Response (Схема: `ArrestResponse`)
- `404` - Player not found
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Arrest By Id (Admin)

Получить арест по ID.

```http
GET /admin/arrests/{arrest_id}
```

**Параметры:**

- `arrest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ArrestResponse`)
- `404` - Arrest not found

---

### Get Arrests By Player (Admin)

Получить все аресты игрока.

```http
GET /admin/arrests/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `active_only` (boolean (optional), default: `false`) - только активные аресты

**Ответы:**

- `200` - Successful Response (Массив: `ArrestResponse`)
- `404` - Player not found

---

### Check Player Arrested (Admin)

Проверить, есть ли у игрока активный арест.

```http
GET /admin/arrests/player/{player_id}/check
```

**Параметры:**

- `player_id` (integer (required)) - Player ID

**Ответы:**

- `200` - Successful Response (объект `{ "is_arrested": bool, "arrest": ArrestResponse | null }`)
- `404` - Player not found

---

### Release Player Endpoint (Admin)

Досрочно освободить игрока из-под ареста.

```http
POST /admin/arrests/{arrest_id}/release
```

**Параметры:**

- `arrest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ArrestResponse`)
- `404` - Arrest not found
- `500` - Internal error

---

### Delete Arrest Endpoint (Admin)

Удалить запись об аресте.

```http
DELETE /admin/arrests/{arrest_id}
```

**Параметры:**

- `arrest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `404` - Arrest not found

---

### Identity by Nick (Moderator)

Получить tg_id и статус привязки по Minecraft-нику.

```http
GET /admin/identity/nick/{nick}
```

**Параметры:** `nick` (string, path) — ник игрока.

**Ответы:** `200` (Схема: `IdentityResponse`), `404` (Player not found), `403` (Moderator access required), `500`.

---

### Identity by Telegram ID (Moderator)

Получить ник и статус привязки по Telegram user ID.

```http
GET /admin/identity/telegram/{tg_id}
```

**Параметры:** `tg_id` (integer, path) — Telegram user ID.

**Ответы:** `200` (Схема: `IdentityResponse`), `404` (Player not found), `403`, `500`.

---

### Identity by Telegram Username

Поиск по Telegram @username. Не реализовано (в модели Player нет поля tg_username).

```http
GET /admin/identity/telegram/username/{username}
```

**Ответы:** `501` (Not implemented).

---

### Unlink Telegram from Player (Moderator)

Отвязать Telegram-аккаунт от игрока по Minecraft-нику (`Player.tg_id` сбрасывается в `NULL`).

```http
POST /admin/identity/nick/{nick}/unlink-telegram
```

**Параметры:** `nick` (string, path) — ник игрока.

**Ответы:** `200` (Схема: `SuccessResponse`), `400` (Player does not have Telegram linked), `404` (Player not found), `403` (Moderator access required), `500`.

---

### Players Search (Support)

Поиск игроков по нику, tg_id или ds_id.

```http
GET /admin/players/search
```

**Параметры:** `query` (string, query, required), `limit` (int, query, default: 20, 1–100).

**Ответы:** `200` (Массив: `PlayerSearchResult`), `403` (Support access required), `500`.

---

### Player Dossier (Support)

Полное досье игрока: профиль, аналитика, транзакции, квесты, клан, друзья.

```http
GET /admin/analytics/player/{player_id}/dossier
```

**Параметры:** `player_id` (integer, path).

**Ответы:** `200` (объект — результат get_player_statistics), `404` (Player not found), `403`, `500`.

---

### Get Bot Settings (Admin)

Получить все настройки бота.

```http
GET /admin/settings
```

**Ответы:** `200` (Схема: `BotSettingsResponse`), `403`, `500`.

---

### Update Bot Settings (Admin)

Обновить настройки бота (слияние с существующими).

```http
PUT /admin/settings
```

**Тело запроса:** Схема: `BotSettingsUpdate`.

**Ответы:** `200` (Схема: `BotSettingsResponse`), `403`, `500`.

---

### Get Bot Setting by Key (Admin)

Получить одну настройку по ключу.

```http
GET /admin/settings/{key}
```

**Параметры:** `key` (string, path).

**Ответы:** `200` (объект `{ "key": "...", "value": "..." }`), `404` (Setting not found), `403`, `500`.

---

### Update Bot Setting by Key (Admin)

Обновить одну настройку. Тело: `{ "value": "..." }`.

```http
PUT /admin/settings/{key}
```

**Параметры:** `key` (string, path). **Тело:** JSON с полем `value` (string).

**Ответы:** `200` (объект key/value), `400` (value is required), `403`, `500`.

---

### Create Vote (Admin)

Создать голосование.

```http
POST /admin/votes
```

**Тело запроса:** Схема: `VoteCreate` (title, description, options, ends_at).

**Ответы:** `201` (Схема: `VoteResponse`), `403`, `500`.

---

### Freeze Wallet (Admin)

Заморозить часть баланса игрока.

```http
POST /admin/wallet/{player_id}/freeze
```

**Параметры:** `player_id` (integer, path). **Тело:** Схема: `WalletFreezeRequest` (amount, reason).

**Ответы:** `200` (Схема: `SuccessResponse`), `400` (Insufficient balance / validation), `404` (Player not found), `403`, `500`.

---

### Unfreeze Wallet (Admin)

Разморозить часть баланса игрока.

```http
POST /admin/wallet/{player_id}/unfreeze
```

**Параметры:** `player_id` (integer, path). **Тело:** Схема: `WalletUnfreezeRequest` (amount).

**Ответы:** `200` (Схема: `SuccessResponse`), `400` (ValueError), `404` (Player not found), `403`, `500`.

---

### Create Server Snapshot (Admin)

Создать снимок состояния сервера.

```http
POST /admin/analytics/server-snapshot
```

**Параметры:** `online_count` (int, query, default: 0), `alive` (bool, query, default: true).

**Ответы:** `200` (объект: id, online_count, alive, timestamp), `403`, `500`.

---

### List Server Snapshots (Admin)

Список снимков сервера с фильтром по датам.

```http
GET /admin/analytics/server-snapshots
```

**Параметры:** `start_date` (datetime, query, optional), `end_date` (datetime, query, optional), `limit` (int, query, default: 100, 1–500).

**Ответы:** `200` (массив объектов снимков), `403`, `500`.

---

### List Player Sessions (Admin)

Список сессий игрока.

```http
GET /admin/analytics/player/{player_id}/sessions
```

**Параметры:** `player_id` (integer, path), `start_date`, `end_date` (datetime, optional), `limit` (int, default: 50, 1–200).

**Ответы:** `200` (массив сессий: id, player_id, start_time, end_time, duration_seconds), `404` (Player not found), `403`, `500`.

---

### Create Player Session (Admin)

Создать или обновить сессию игрока (для сбора метрик). Тело: start_time, end_time, duration.

```http
POST /admin/analytics/player/{player_id}/session
```

**Параметры:** `player_id` (integer, path). **Тело:** опционально JSON с полями start_time, end_time, duration.

**Ответы:** `200` (объект сессии), `404` (Player not found), `403`, `500`.

---

### Get Referrals Stats (Admin)

Агрегированная статистика по рефералам.

```http
GET /admin/referrals/stats
```

**Ответы:** `200` (объект от get_all_referral_stats), `403`, `500`.

---

### List Nick Change Requests (Moderator)

Список заявок на смену ника.

```http
GET /admin/nickchange/requests
```

**Параметры:** `status` (string, query, optional), `limit` (int, default: 50, 1–100), `offset` (int, default: 0).

**Ответы:** `200` (Массив: `NickChangeRequestResponse`), `403`, `500`.

---

### Approve Nick Change (Moderator)

Одобрить заявку на смену ника.

```http
POST /admin/nickchange/{request_id}/approve
```

**Параметры:** `request_id` (integer, path).

**Ответы:** `200` (Схема: `SuccessResponse`), `400` (ValueError), `403`, `500`.

---

### Reject Nick Change (Moderator)

Отклонить заявку на смену ника.

```http
POST /admin/nickchange/{request_id}/reject
```

**Параметры:** `request_id` (integer, path).

**Ответы:** `200` (Схема: `SuccessResponse`), `400` (ValueError), `403`, `500`.

---

## SAFETY Endpoints

### Create Ban

Create a ban for a player

```http
POST /admin/bans
```

**Параметры:**


**Тело запроса:**

Схема: `BanCreate`

**Ответы:**

- `201` - Successful Response (Схема: `BanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Bans By Player

Get all bans for a player

```http
GET /admin/bans/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `active_only` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `BanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Check Player Banned

Check if player is currently banned

```http
GET /admin/bans/player/{player_id}/check
```

**Параметры:**

- `player_id` (integer (required)) - Player ID

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Ban Endpoint

Delete a ban

```http
DELETE /admin/bans/{ban_id}
```

**Параметры:**

- `ban_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Ban By Id

Get ban by ID

```http
GET /admin/bans/{ban_id}
```

**Параметры:**

- `ban_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `BanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Unban Player Endpoint

Unban a player

```http
POST /admin/bans/{ban_id}/unban
```

**Параметры:**

- `ban_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `BanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Admin Logs Endpoint

Get admin action logs

```http
GET /admin/logs
```

**Параметры:**

- `admin_id` (string (optional)) - No description
- `action_type` (string (optional)) - No description
- `limit` (integer (optional)) - No description
- `offset` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `AdminActionLogResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Player Logs

Get admin logs for a specific player

```http
GET /admin/logs/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `limit` (integer (optional)) - No description
- `offset` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `AdminActionLogResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Mute

Create a mute for a player

```http
POST /admin/mutes
```

**Параметры:**


**Тело запроса:**

Схема: `MuteCreate`

**Ответы:**

- `201` - Successful Response (Схема: `MuteResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Mutes By Player

Get all mutes for a player

```http
GET /admin/mutes/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `active_only` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `MuteResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Check Player Muted

Check if player is currently muted

```http
GET /admin/mutes/player/{player_id}/check
```

**Параметры:**

- `player_id` (integer (required)) - Player ID

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Mute Endpoint

Delete a mute

```http
DELETE /admin/mutes/{mute_id}
```

**Параметры:**

- `mute_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Mute By Id

Get mute by ID

```http
GET /admin/mutes/{mute_id}
```

**Параметры:**

- `mute_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `MuteResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Unmute Player Endpoint

Unmute a player

```http
POST /admin/mutes/{mute_id}/unmute
```

**Параметры:**

- `mute_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `MuteResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Warn

Create a warn for a player

```http
POST /admin/warns
```

**Параметры:**


**Тело запроса:**

Схема: `WarnCreate`

**Ответы:**

- `201` - Successful Response (Схема: `WarnResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Warns By Player

Get all warns for a player

```http
GET /admin/warns/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `active_only` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `WarnResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Warn Endpoint

Delete a warn

```http
DELETE /admin/warns/{warn_id}
```

**Параметры:**

- `warn_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Warn By Id

Get warn by ID

```http
GET /admin/warns/{warn_id}
```

**Параметры:**

- `warn_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `WarnResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Arrest

Create an arrest for a player. Подробнее см. [docs/ARRESTS.md](docs/ARRESTS.md).

```http
POST /admin/arrests
```

**Тело запроса:**

Схема: `ArrestCreate`

**Ответы:**

- `201` - Successful Response (Схема: `ArrestResponse`)
- `404` - Player not found
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Arrest By Id

Get arrest by ID

```http
GET /admin/arrests/{arrest_id}
```

**Параметры:**

- `arrest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ArrestResponse`)
- `404` - Arrest not found

---

### Get Arrests By Player

Get all arrests for a player

```http
GET /admin/arrests/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - Player ID
- `active_only` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ArrestResponse`)
- `404` - Player not found

---

### Check Player Arrested

Check if player is currently arrested

```http
GET /admin/arrests/player/{player_id}/check
```

**Параметры:**

- `player_id` (integer (required)) - Player ID

**Ответы:**

- `200` - Successful Response
- `404` - Player not found

---

### Release Player Endpoint

Release a player from arrest (early release)

```http
POST /admin/arrests/{arrest_id}/release
```

**Параметры:**

- `arrest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ArrestResponse`)
- `404` - Arrest not found

---

### Delete Arrest Endpoint

Delete an arrest record

```http
DELETE /admin/arrests/{arrest_id}
```

**Параметры:**

- `arrest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `404` - Arrest not found

---

## MANAGEMENT Endpoints

### Create Announcement Endpoint

Create a new announcement

```http
POST /admin/announcements
```

**Параметры:**


**Тело запроса:**

Схема: `AnnouncementCreate`

**Ответы:**

- `201` - Successful Response (Схема: `AnnouncementResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Announcement Endpoint

Delete an announcement

```http
DELETE /admin/announcements/{announcement_id}
```

**Параметры:**

- `announcement_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Announcement Endpoint

Update an announcement

```http
PUT /admin/announcements/{announcement_id}
```

**Параметры:**

- `announcement_id` (integer (required)) - No description

**Тело запроса:**

Схема: `AnnouncementUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `AnnouncementResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Bulk Notification Endpoint

Send bulk notifications

```http
POST /admin/notifications/bulk
```

**Параметры:**


**Тело запроса:**

Схема: `NotificationBulkCreate`

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Send Notification To Role Endpoint

Send notification to all players with specific role

```http
POST /admin/notifications/role
```

**Параметры:**

- `role` (string (required)) - No description
- `title` (string (required)) - No description
- `content` (string (required)) - No description
- `notification_type` (string (optional)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Economy Statistics Endpoint

Get economy statistics for a date range

```http
GET /admin/statistics/economy
```

**Параметры:**

- `start_date` (string (optional)) - No description
- `end_date` (string (optional)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Player Statistics Endpoint

Get comprehensive statistics for a player

```http
GET /admin/statistics/player/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Server Statistics Endpoint

Get server-wide statistics

```http
GET /admin/statistics/server
```

**Параметры:**


**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## USER Endpoints

### Get Analytics Endpoint

Get player analytics

```http
GET /user/analytics
```

**Параметры:**


**Ответы:**

- `200` - Successful Response (Схема: `PlayerAnalyticsResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Analytics Endpoint

Update player analytics

```http
PUT /user/analytics
```

**Параметры:**


**Тело запроса:**

Схема: `PlayerAnalyticsUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `PlayerAnalyticsResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Add Social Link Endpoint

Add social link to player analytics

```http
POST /user/analytics/socials
```

**Параметры:**


**Тело запроса:**

Схема: `SocialLinkAdd`

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Remove Social Link Endpoint

Remove social link from player analytics

```http
DELETE /user/analytics/socials/{social_name}
```

**Параметры:**

- `social_name` (string (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Announcements Endpoint

Get active announcements for player

```http
GET /user/announcements
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `AnnouncementResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Announcement Endpoint

Get announcement by ID

```http
GET /user/announcements/{announcement_id}
```

**Параметры:**

- `announcement_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `AnnouncementResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Clans Endpoint

Get clans with optional filters

```http
GET /user/clans
```

**Параметры:**

- `name` (string (optional)) - No description
- `tag` (string (optional)) - No description
- `search` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Clan Endpoint

Create a new clan

```http
POST /user/clans
```

**Параметры:**


**Тело запроса:**

Схема: `ClanCreate`

**Ответы:**

- `201` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Clan Endpoint

Delete clan (only owner)

```http
DELETE /user/clans/{clan_id}
```

**Параметры:**

- `clan_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Clan Endpoint

Get clan by ID

```http
GET /user/clans/{clan_id}
```

**Параметры:**

- `clan_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Clan Endpoint

Update clan (only owner or moderator)

```http
PUT /user/clans/{clan_id}
```

**Параметры:**

- `clan_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ClanUpdate`. Обновление инвентаря отключено: поле `inventory` в теле не принимается (422 при передаче).

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Add Clan Member Endpoint

Add member to clan (only owner or moderator)

```http
POST /user/clans/{clan_id}/members
```

**Параметры:**

- `clan_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ClanMemberAdd`

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Remove Clan Member Endpoint

Remove member from clan (выход из клана или кик). У удалённого игрока в аналитике сбрасывается привязка к клану (`clan_id`).

```http
DELETE /user/clans/{clan_id}/members/{member_id}
```

**Параметры:**

- `clan_id` (integer (required)) - No description
- `member_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Clan Member Role Endpoint

Update clan member role (only owner)

```http
PUT /user/clans/{clan_id}/members/{member_id}/role
```

**Параметры:**

- `clan_id` (integer (required)) - No description
- `member_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ClanMemberUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Crafts Endpoint

Get all crafts

```http
GET /user/crafts
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `CraftResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Crafts By Item Endpoint

Get crafts that use a specific item

```http
GET /user/crafts/by-item/{item_id}
```

**Параметры:**

- `item_id` (string (required)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `CraftResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Craft Endpoint

Get craft by ID

```http
GET /user/crafts/{craft_id}
```

**Параметры:**

- `craft_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `CraftResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Check Can Craft Endpoint

Check if player can craft this item

```http
GET /user/crafts/{craft_id}/can-craft
```

**Параметры:**

- `craft_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Friends Endpoint

Get player's friends

```http
GET /user/friends
```

**Параметры:**


**Ответы:**

- `200` - Successful Response (Массив: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Mutual Friends Endpoint

Get mutual friends with another player

```http
GET /user/friends/mutual/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `MutualFriendsResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Send Friend Request Endpoint

Send friend request

```http
POST /user/friends/request
```

**Параметры:**


**Тело запроса:**

Схема: `FriendRequest`

**Ответы:**

- `201` - Successful Response (Схема: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Friend Requests Endpoint

Get friend requests (incoming or outgoing)

```http
GET /user/friends/requests
```

**Параметры:**

- `incoming` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Friend Suggestions Endpoint

Get friend suggestions

```http
GET /user/friends/suggestions
```

**Параметры:**

- `limit` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Remove Friend Endpoint

Remove friend

```http
DELETE /user/friends/{friend_id}
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Accept Friend Request Endpoint

Accept friend request

```http
POST /user/friends/{friend_id}/accept
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Block Friend Endpoint

Block friend

```http
POST /user/friends/{friend_id}/block
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Reject Friend Request Endpoint

Reject friend request

```http
POST /user/friends/{friend_id}/reject
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Unblock Friend Endpoint

Unblock friend

```http
POST /user/friends/{friend_id}/unblock
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Market Items Endpoint

Get market items with optional filters

```http
GET /user/market/items
```

**Параметры:**

- `seller_id` (string (optional)) - No description
- `item_id` (string (optional)) - No description
- `search` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `MarketItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Market Item Endpoint

Create a new market item

```http
POST /user/market/items
```

**Параметры:**


**Тело запроса:**

Схема: `MarketItemCreate`

**Ответы:**

- `201` - Successful Response (Схема: `MarketItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Market Item Endpoint

Delete market item (only seller)

```http
DELETE /user/market/items/{item_id}
```

**Параметры:**

- `item_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Market Item Endpoint

Get market item by ID

```http
GET /user/market/items/{item_id}
```

**Параметры:**

- `item_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `MarketItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Market Item Endpoint

Update market item (only seller)

```http
PUT /user/market/items/{item_id}
```

**Параметры:**

- `item_id` (integer (required)) - No description

**Тело запроса:**

Схема: `MarketItemUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `MarketItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Notifications Endpoint

Get player notifications

```http
GET /user/notifications
```

**Параметры:**

- `is_read` (boolean (optional)) - No description
- `notification_type` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `NotificationResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Mark All Notifications Read Endpoint

Mark all notifications as read

```http
POST /user/notifications/read-all
```

**Параметры:**


**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Unread Notifications Endpoint

Get unread notifications

```http
GET /user/notifications/unread
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `NotificationResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Unread Count Endpoint

Get count of unread notifications

```http
GET /user/notifications/unread-count
```

**Параметры:**


**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Notification Endpoint

Delete notification

```http
DELETE /user/notifications/{notification_id}
```

**Параметры:**

- `notification_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Mark Notification Read Endpoint

Mark notification as read

```http
POST /user/notifications/{notification_id}/read
```

**Параметры:**

- `notification_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `NotificationResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Npcs Endpoint

Get all NPCs

```http
GET /user/npcs
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `NPCResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Npcs By Location Endpoint

Get NPCs by location

```http
GET /user/npcs/location
```

**Параметры:**

- `dim` (string (required)) - No description
- `x` (number (required)) - No description
- `y` (number (required)) - No description
- `z` (number (required)) - No description
- `radius` (number (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `NPCResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Npc Endpoint

Get NPC by ID

```http
GET /user/npcs/{npc_id}
```

**Параметры:**

- `npc_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `NPCResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Npc Dialog Endpoint

Get NPC dialog by message ID

```http
GET /user/npcs/{npc_id}/dialog/{message_id}
```

**Параметры:**

- `npc_id` (integer (required)) - No description
- `message_id` (string (required)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Parties Endpoint

Get parties

```http
GET /user/parties
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Party Endpoint

Create a new party

```http
POST /user/parties
```

**Параметры:**


**Тело запроса:**

Схема: `PartyCreate`

**Ответы:**

- `201` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Party Endpoint

Delete party (only leader)

```http
DELETE /user/parties/{party_id}
```

**Параметры:**

- `party_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Party Endpoint

Get party by ID

```http
GET /user/parties/{party_id}
```

**Параметры:**

- `party_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Party Endpoint

Update party (only leader)

```http
PUT /user/parties/{party_id}
```

**Параметры:**

- `party_id` (integer (required)) - No description

**Тело запроса:**

Схема: `PartyUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Add Party Member Endpoint

Add member to party

```http
POST /user/parties/{party_id}/members
```

**Параметры:**

- `party_id` (integer (required)) - No description

**Тело запроса:**

Схема: `PartyMemberAdd`

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Remove Party Member Endpoint

Remove member from party

```http
DELETE /user/parties/{party_id}/members/{member_id}
```

**Параметры:**

- `party_id` (integer (required)) - No description
- `member_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Transfer Party Leadership Endpoint

Transfer party leadership (only current leader)

```http
POST /user/parties/{party_id}/transfer-leadership
```

**Параметры:**

- `party_id` (integer (required)) - No description
- `new_leader_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Profile by Nickname Endpoint

Get player profile by nickname. Аутентификация не требуется (`X-Player-ID` не нужен). Если игрок существует, но у него ещё нет профиля, профиль (и analytics) создаются автоматически, чтобы эндпоинт вернул `200` вместо `404`.

```http
GET /user/profile/by-nickname/{nickname}
```

**Параметры:**

- `nickname` (string (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `PlayerProfileResponse`)
- `404` - Player not found
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Profile Endpoint

Get player profile

```http
GET /user/profile
```

**Параметры:**


**Ответы:**

- `200` - Successful Response (Схема: `PlayerProfileResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Profile Endpoint

Create player profile

```http
POST /user/profile
```

**Параметры:**


**Тело запроса:**

Схема: `PlayerProfileUpdate`

**Ответы:**

- `201` - Successful Response (Схема: `PlayerProfileResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Profile Endpoint

Update player profile

```http
PUT /user/profile
```

**Параметры:**


**Тело запроса:**

Схема: `PlayerProfileUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `PlayerProfileResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get My Sessions Endpoint

Get current player's play sessions (no admin required).

```http
GET /user/sessions
```

**Параметры:**

- `start_date` (datetime (optional)) - No description
- `end_date` (datetime (optional)) - No description
- `limit` (integer (optional), default: `50`, 1–200) - No description

**Ответы:**

- `200` - Successful Response (массив объектов сессий: `id`, `player_id`, `start_time`, `end_time`, `duration_seconds`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Link Telegram Endpoint

Привязать Telegram-аккаунт к текущему игроку. Один `tg_id` не может быть привязан к разным игрокам.

```http
POST /user/profile/telegram/link
```

**Тело запроса:**

Схема: `TelegramLinkRequest` (`tg_id`: int — Telegram user ID)

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `400` - Неверный запрос
- `409` - Этот Telegram уже привязан к другому аккаунту
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### List Votes Endpoint

Список активных голосований.

```http
GET /user/votes
```

**Параметры:** `limit` (int, query, default: 50).

**Ответы:** `200` (Массив: `VoteResponse`), `500`.

---

### Get Vote Endpoint

Получить голосование по ID с текущей статистикой.

```http
GET /user/votes/{vote_id}
```

**Параметры:** `vote_id` (integer, path).

**Ответы:** `200` (Схема: `VoteResponse`), `404` (Vote not found), `500`.

---

### Cast Vote Endpoint

Отдать голос. Требуется не менее 1 часа игрового времени.

```http
POST /user/votes/{vote_id}/vote
```

**Параметры:** `vote_id` (integer, path). **Тело:** Схема: `VoteCastRequest` (option_id).

**Ответы:** `200` (Схема: `VoteResponse`), `400` (Invalid option), `403` (требуется 1 hour playtime), `404` (Vote not found), `409` (Already voted), `500`.

---

### Get Vote Stats Endpoint

Статистика по голосованию (количество голосов и проценты по вариантам).

```http
GET /user/votes/{vote_id}/stats
```

**Параметры:** `vote_id` (integer, path).

**Ответы:** `200` (Схема: `VoteStatsResponse`), `404` (Vote not found), `500`.

---

### Get Rankings Balance Endpoint

Рейтинг игроков по балансу.

```http
GET /user/rankings/balance
```

**Параметры:** `limit` (int, query, default: 10, 1–100), `offset` (int, query, default: 0).

**Ответы:** `200` (Массив: `RankingBalanceEntry`), `500`.

---

### Get Rankings Online Time Endpoint

Рейтинг игроков по суммарному времени онлайн (секунды).

```http
GET /user/rankings/online-time
```

**Параметры:** `limit` (int, query, default: 10, 1–100), `offset` (int, query, default: 0).

**Ответы:** `200` (Массив: `RankingOnlineTimeEntry`), `500`.

---

### Get Referral Code Endpoint

Получить или создать свой реферальный код.

```http
GET /user/referrals/code
```

**Ответы:** `200` (Схема: `ReferralCodeResponse`), `500`.

---

### Join Referral Endpoint

Присоединиться по реферальному коду.

```http
POST /user/referrals/join
```

**Тело запроса:** Схема: `ReferralJoinRequest` (code).

**Ответы:** `200` (Схема: `SuccessResponse`), `400` (ValueError), `500`.

---

### Get Referral Stats Endpoint

Статистика реферала текущего игрока.

```http
GET /user/referrals/stats
```

**Ответы:** `200` (Схема: `ReferralStatsResponse`), `500`.

---

### Nick Change Request Endpoint

Подать заявку на смену ника.

```http
POST /user/nickchange/request
```

**Тело запроса:** Схема: `NickChangeRequestCreate` (new_nick).

**Ответы:** `200` (Схема: `NickChangeRequestResponse`), `400` (ValueError), `500`.

---

### Nick Change History Endpoint

История заявок на смену ника текущего игрока.

```http
GET /user/nickchange/history
```

**Ответы:** `200` (объект `{ "history": ... }`), `500`.

---

### Create Player Quest Endpoint

Создать квест от игрока; награда удерживается с баланса создателя.

```http
POST /user/quests/create
```

**Тело запроса:** Схема: `PlayerQuestCreate` (title, description, reward).

**Ответы:** `201` (Схема: `PlayerQuestResponse`), `400` (ValueError, например недостаточно баланса), `500`.

---

### List Player-Created Quests Endpoint

Список квестов, созданных игроками.

```http
GET /user/quests/player-created
```

**Параметры:** `creator_id` (int, optional), `status` (string, optional), `limit` (int, default: 50, 1–100), `offset` (int, default: 0).

**Ответы:** `200` (Массив: `PlayerQuestResponse`), `500`.

---

### Get Player Quest Endpoint

Получить детали задания.

```http
GET /user/quests/{quest_id}
```

**Параметры:** `quest_id` (integer, path).

**Ответы:** `200` (Схема: `PlayerQuestResponse`), `404` (Quest not found), `500`.

---

### Create Player Quest Application Endpoint

Создать отклик на задание.

```http
POST /user/quests/{quest_id}/applications
```

**Параметры:** `quest_id` (integer, path). **Тело:** Схема: `PlayerQuestApplicationCreate`.

**Ответы:** `201` (Схема: `PlayerQuestApplicationResponse`), `400`, `404`, `500`.

---

### List Player Quest Applications Endpoint

Получить список откликов на задание. Полный список доступен только владельцу задания.

```http
GET /user/quests/{quest_id}/applications
```

**Параметры:** `quest_id` (integer, path).

**Ответы:** `200` (Массив: `PlayerQuestApplicationResponse`), `403`, `404`, `500`.

---

### List My Player Quest Applications Endpoint

Список моих откликов на задания.

```http
GET /user/quests/applications/mine
```

**Параметры:** `status` (string, optional), `limit` (int, default: 50, 1–100), `offset` (int, default: 0).

**Ответы:** `200` (Массив: `PlayerQuestApplicationResponse`), `500`.

---

### Accept Player Quest Application Endpoint

Выбрать исполнителя по отклику.

```http
POST /user/quests/{quest_id}/applications/{application_id}/accept
```

**Параметры:** `quest_id` (integer, path), `application_id` (integer, path).

**Ответы:** `200` (Схема: `PlayerQuestResponse`), `400`, `403`, `404`, `500`.

---

### Reject Player Quest Application Endpoint

Отклонить отклик.

```http
POST /user/quests/{quest_id}/applications/{application_id}/reject
```

**Параметры:** `quest_id` (integer, path), `application_id` (integer, path). **Тело:** Схема: `PlayerQuestReviewRequest`.

**Ответы:** `200` (Схема: `PlayerQuestApplicationResponse`), `400`, `403`, `404`, `500`.

---

### Withdraw Player Quest Application Endpoint

Отозвать свой отклик.

```http
POST /user/quests/{quest_id}/applications/{application_id}/withdraw
```

**Параметры:** `quest_id` (integer, path), `application_id` (integer, path).

**Ответы:** `200` (Схема: `PlayerQuestApplicationResponse`), `400`, `403`, `404`, `500`.

---

### Submit Player Quest Result Endpoint

Отправить результат задания на проверку.

```http
POST /user/quests/{quest_id}/submit
```

**Параметры:** `quest_id` (integer, path). **Тело:** Схема: `PlayerQuestSubmissionRequest`.

**Ответы:** `200` (Схема: `PlayerQuestResponse`), `400`, `403`, `404`, `500`.

---

### Approve Player Quest Endpoint

Принять работу и выплатить награду исполнителю.

```http
POST /user/quests/{quest_id}/approve
```

**Параметры:** `quest_id` (integer, path).

**Ответы:** `200` (Схема: `PlayerQuestResponse`), `400`, `403`, `404`, `500`.

---

### Request Player Quest Changes Endpoint

Вернуть задание на доработку.

```http
POST /user/quests/{quest_id}/request-changes
```

**Параметры:** `quest_id` (integer, path). **Тело:** Схема: `PlayerQuestReviewRequest`.

**Ответы:** `200` (Схема: `PlayerQuestResponse`), `400`, `403`, `404`, `500`.

---

### Abandon Player Quest Endpoint

Отказаться от выполнения выбранного задания.

```http
POST /user/quests/{quest_id}/abandon
```

**Параметры:** `quest_id` (integer, path).

**Ответы:** `200` (Схема: `PlayerQuestResponse`), `400`, `403`, `404`, `500`.

---

### Cancel Player Quest Endpoint

Отменить квест (только создатель); награда возвращается создателю.

```http
POST /user/quests/{quest_id}/cancel
```

**Параметры:** `quest_id` (integer, path).

**Ответы:** `200` (Схема: `PlayerQuestResponse`), `400` (ValueError), `403` (Only creator can cancel), `404` (Quest not found), `500`.

---

### Delete Player Quest Endpoint

Удалить задание без активного исполнителя.

```http
DELETE /user/quests/{quest_id}
```

**Параметры:** `quest_id` (integer, path).

**Ответы:** `200` (Схема: `SuccessResponse`), `400`, `403`, `404`, `500`.

---

### Get Quests Endpoint

Get active quests

```http
GET /user/quests
```

**Параметры:**

- `quest_type` (string (optional)) - No description
- `search` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `QuestResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Quest Recommendations Endpoint

Get quest recommendations for player

```http
GET /user/quests/recommendations
```

**Параметры:**

- `limit` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `QuestResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Quest Statistics Endpoint

Get player quest statistics

```http
GET /user/quests/statistics
```

**Параметры:**


**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Quest Endpoint

Get quest by ID

```http
GET /user/quests/{quest_id}
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `QuestResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Claim Quest Reward Endpoint

Claim quest reward

```http
POST /user/quests/{quest_id}/claim
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `QuestProgressResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Complete Quest Endpoint

Complete a quest

```http
POST /user/quests/{quest_id}/complete
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `QuestProgressResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Quest Progress Endpoint

Get quest progress for player

```http
GET /user/quests/{quest_id}/progress
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `QuestProgressResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Start Quest Endpoint

Start a quest

```http
POST /user/quests/{quest_id}/start
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `201` - Successful Response (Схема: `QuestProgressResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Scenarios Endpoint

Get scenarios

```http
GET /user/scenarios
```

**Параметры:**

- `scenario_type` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ScenarioResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Scenario Endpoint

Get scenario by ID

```http
GET /user/scenarios/{scenario_id}
```

**Параметры:**

- `scenario_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ScenarioResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Execute Scenario Endpoint

Execute a scenario

```http
POST /user/scenarios/{scenario_id}/execute
```

**Параметры:**

- `scenario_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ScenarioExecute`

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Shops Endpoint

Get shops

```http
GET /user/shops
```

**Параметры:**

- `owner_id` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ShopResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Shop Endpoint

Create a new shop

```http
POST /user/shops
```

**Параметры:**


**Тело запроса:**

Схема: `ShopCreate`

**Ответы:**

- `201` - Successful Response (Схема: `ShopResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Shop Endpoint

Delete shop (only owner)

```http
DELETE /user/shops/{shop_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Shop Endpoint

Get shop by ID with items

```http
GET /user/shops/{shop_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ShopWithItemsResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Shop Endpoint

Update shop (only owner)

```http
PUT /user/shops/{shop_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `ShopResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Shop Items Endpoint

Get shop items

```http
GET /user/shops/{shop_id}/items
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ShopItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Shop Item Endpoint

Create shop item (only owner)

```http
POST /user/shops/{shop_id}/items
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopItemCreate`

**Ответы:**

- `201` - Successful Response (Схема: `ShopItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Full Sync Shop Items Endpoint

Full replace/sync of shop items from external source of truth (только владелец). Принимает полный список позиций магазина и приводит `ShopItem`/`Shop.inventory` в соответствие: создаёт отсутствующие, обновляет существующие (по `item_id` + `item_nbt`), удаляет позиции, которых нет в присланном списке.

```http
PUT /user/shops/{shop_id}/items/full-sync
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopItemsFullSyncRequest` (`items`: массив `ShopItemCreate`)

**Ответы:**

- `200` - Successful Response (Схема: `ShopItemsFullSyncResponse`: `created`, `updated`, `deleted`, `total`, `items`)
- `400` - ValueError (Схема: `HTTPValidationError`-подобная ошибка от менеджера)
- `403` - Only owner can sync items
- `404` - Shop not found
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Buy Shop Item Endpoint

Buy item from shop (checks balance, transfers money to owner, decreases quantity). Логируется транзакция покупки. Подробнее см. [docs/SHOPS.md](docs/SHOPS.md).

```http
POST /user/shops/{shop_id}/items/{item_id}/buy
```

**Параметры:**

- `shop_id` (integer (required)) - No description
- `item_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopItemBuy` (`quantity`, default: `1`)

**Ответы:**

- `200` - Successful Response (Схема: `ShopPurchaseResponse`: `shop_item_id`, `item_id`, `quantity`, `total_paid`, `remaining_total_count`)
- `400` - Quantity must be at least 1 / Insufficient quantity / other ValueError
- `402` - Insufficient balance
- `404` - Shop item not found
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Shop Item Endpoint

Delete shop item (only owner)

```http
DELETE /user/shops/{shop_id}/items/{item_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description
- `item_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Shop Item Endpoint

Update shop item (only owner). Можно обновить цену, размер лота, остаток (`total_count`) и NBT предмета (`item_nbt`). Остаток допускается задавать любым значением (в т.ч. увеличивать).

```http
PUT /user/shops/{shop_id}/items/{item_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description
- `item_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopItemUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `ShopItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Balance Endpoint

Получить баланс текущего игрока. В ответе возвращаются поля `balance` и `frozen` (замороженная сумма); доступный баланс = balance − frozen.

```http
GET /user/balance
```

**Ответы:** `200` (Схема: `BalanceResponse`: balance, frozen), `401`, `404`, `500`.

---

### Daily Reward Endpoint

Получить ежедневную награду (daily) для текущего игрока. Используется командой в TG-боте.

```http
POST /user/daily
```

Также доступен совместимый путь: `POST /user/economics/daily`.

**Правила серии:**

- daily можно получить не чаще чем раз в 24 часа;
- если с прошлого daily прошло \>= 24ч и \< 48ч — серия (`streak_days`) увеличивается на 1;
- если прошло \>= 48ч — серия сбрасывается и становится 1;
- множитель награды: `multiplier = min(1.0 + 0.1 * streak_days, 2.0)`;
- итоговая награда: `final_amount = int(base_amount * multiplier)`, где `base_amount` — случайное число в диапазоне `[50, 150]`.

**Ответ 200 (Схема: `DailyRewardResponse`):**

- `base_amount` — базовая случайная награда до множителя;
- `streak_days` — текущая длина серии daily;
- `streak_max` — максимальная достигнутая серия daily;
- `multiplier` — применённый множитель (не больше 2.0);
- `final_amount` — фактически начисленные вайши;
- `next_available_at` — время (ISO datetime), когда можно снова вызвать daily;
- `balance_after` — баланс игрока после начисления.

**Ответ 429:** daily уже был получен менее 24 часов назад. В `detail.next_available_at` вернётся время следующего доступного получения награды.

---

### Get Transactions Endpoint

Get player transactions with filters

```http
GET /user/transactions
```

**Параметры:**

- `transaction_type` (string (optional)) - No description
- `start_date` (string (optional)) - No description
- `end_date` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `TransactionResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Transaction Endpoint

Create a new transaction

```http
POST /user/transactions
```

**Параметры:**


**Тело запроса:**

Схема: `TransactionCreate`

**Ответы:**

- `201` - Successful Response (Схема: `TransactionResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Transfer Endpoint

Перевод вайш от текущего игрока другому. Отправитель определяется по `X-Player-ID`. Схема: `TransferCreate` (to_player_id, amount, description). Подробнее см. [docs/TRANSFERS.md](docs/TRANSFERS.md).

```http
POST /user/transactions/transfer
```

**Тело запроса:** Схема: `TransferCreate`.

**Ответы:** `201` (Схема: `TransferResponse`), `400` (нарушение правил), `402` (Insufficient balance), `404` (To player not found / profile not found), `401`, `500`.

---

### Get Balance History Endpoint

Get player balance history

```http
GET /user/transactions/balance-history
```

**Параметры:**

- `days` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Top Players Endpoint

Get top players by balance

```http
GET /user/transactions/top-players
```

**Параметры:**

- `limit` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Transaction Endpoint

Get transaction by ID

```http
GET /user/transactions/{transaction_id}
```

**Параметры:**

- `transaction_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `TransactionResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## ECONOMICS Endpoints

### Get Quests Endpoint

Get active quests

```http
GET /user/quests
```

**Параметры:**

- `quest_type` (string (optional)) - No description
- `search` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `QuestResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Quest Recommendations Endpoint

Get quest recommendations for player

```http
GET /user/quests/recommendations
```

**Параметры:**

- `limit` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `QuestResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Quest Statistics Endpoint

Get player quest statistics

```http
GET /user/quests/statistics
```

**Параметры:**


**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Quest Endpoint

Get quest by ID

```http
GET /user/quests/{quest_id}
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `QuestResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Claim Quest Reward Endpoint

Claim quest reward

```http
POST /user/quests/{quest_id}/claim
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `QuestProgressResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Complete Quest Endpoint

Complete a quest

```http
POST /user/quests/{quest_id}/complete
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `QuestProgressResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Quest Progress Endpoint

Get quest progress for player

```http
GET /user/quests/{quest_id}/progress
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `QuestProgressResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Start Quest Endpoint

Start a quest

```http
POST /user/quests/{quest_id}/start
```

**Параметры:**

- `quest_id` (integer (required)) - No description

**Ответы:**

- `201` - Successful Response (Схема: `QuestProgressResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Transactions Endpoint

Get player transactions with filters

```http
GET /user/transactions
```

**Параметры:**

- `transaction_type` (string (optional)) - No description
- `start_date` (string (optional)) - No description
- `end_date` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `TransactionResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Transaction Endpoint

Create a new transaction

```http
POST /user/transactions
```

**Параметры:**


**Тело запроса:**

Схема: `TransactionCreate`

**Ответы:**

- `201` - Successful Response (Схема: `TransactionResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Balance History Endpoint

Get player balance history

```http
GET /user/transactions/balance-history
```

**Параметры:**

- `days` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Top Players Endpoint

Get top players by balance

```http
GET /user/transactions/top-players
```

**Параметры:**

- `limit` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Transaction Endpoint

Get transaction by ID

```http
GET /user/transactions/{transaction_id}
```

**Параметры:**

- `transaction_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `TransactionResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## SOCIAL Endpoints

### Get Friends Endpoint

Get player's friends

```http
GET /user/friends
```

**Параметры:**


**Ответы:**

- `200` - Successful Response (Массив: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Mutual Friends Endpoint

Get mutual friends with another player

```http
GET /user/friends/mutual/{player_id}
```

**Параметры:**

- `player_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `MutualFriendsResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Send Friend Request Endpoint

Send friend request

```http
POST /user/friends/request
```

**Параметры:**


**Тело запроса:**

Схема: `FriendRequest`

**Ответы:**

- `201` - Successful Response (Схема: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Friend Requests Endpoint

Get friend requests (incoming or outgoing)

```http
GET /user/friends/requests
```

**Параметры:**

- `incoming` (boolean (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Friend Suggestions Endpoint

Get friend suggestions

```http
GET /user/friends/suggestions
```

**Параметры:**

- `limit` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Remove Friend Endpoint

Remove friend

```http
DELETE /user/friends/{friend_id}
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Accept Friend Request Endpoint

Accept friend request

```http
POST /user/friends/{friend_id}/accept
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Block Friend Endpoint

Block friend

```http
POST /user/friends/{friend_id}/block
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `FriendResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Reject Friend Request Endpoint

Reject friend request

```http
POST /user/friends/{friend_id}/reject
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Unblock Friend Endpoint

Unblock friend

```http
POST /user/friends/{friend_id}/unblock
```

**Параметры:**

- `friend_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## MAILING Endpoints

### Get Announcements Endpoint

Get active announcements for player

```http
GET /user/announcements
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `AnnouncementResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Announcement Endpoint

Get announcement by ID

```http
GET /user/announcements/{announcement_id}
```

**Параметры:**

- `announcement_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `AnnouncementResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Notifications Endpoint

Get player notifications

```http
GET /user/notifications
```

**Параметры:**

- `is_read` (boolean (optional)) - No description
- `notification_type` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `NotificationResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Mark All Notifications Read Endpoint

Mark all notifications as read

```http
POST /user/notifications/read-all
```

**Параметры:**


**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Unread Notifications Endpoint

Get unread notifications

```http
GET /user/notifications/unread
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `NotificationResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Unread Count Endpoint

Get count of unread notifications

```http
GET /user/notifications/unread-count
```

**Параметры:**


**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Notification Endpoint

Delete notification

```http
DELETE /user/notifications/{notification_id}
```

**Параметры:**

- `notification_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Mark Notification Read Endpoint

Mark notification as read

```http
POST /user/notifications/{notification_id}/read
```

**Параметры:**

- `notification_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `NotificationResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## QOL Endpoints

### Get Crafts Endpoint

Get all crafts

```http
GET /user/crafts
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `CraftResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Crafts By Item Endpoint

Get crafts that use a specific item

```http
GET /user/crafts/by-item/{item_id}
```

**Параметры:**

- `item_id` (string (required)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `CraftResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Craft Endpoint

Get craft by ID

```http
GET /user/crafts/{craft_id}
```

**Параметры:**

- `craft_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `CraftResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Check Can Craft Endpoint

Check if player can craft this item

```http
GET /user/crafts/{craft_id}/can-craft
```

**Параметры:**

- `craft_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Npcs Endpoint

Get all NPCs

```http
GET /user/npcs
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `NPCResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Npcs By Location Endpoint

Get NPCs by location

```http
GET /user/npcs/location
```

**Параметры:**

- `dim` (string (required)) - No description
- `x` (number (required)) - No description
- `y` (number (required)) - No description
- `z` (number (required)) - No description
- `radius` (number (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `NPCResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Npc Endpoint

Get NPC by ID

```http
GET /user/npcs/{npc_id}
```

**Параметры:**

- `npc_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `NPCResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Npc Dialog Endpoint

Get NPC dialog by message ID

```http
GET /user/npcs/{npc_id}/dialog/{message_id}
```

**Параметры:**

- `npc_id` (integer (required)) - No description
- `message_id` (string (required)) - No description

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Scenarios Endpoint

Get scenarios

```http
GET /user/scenarios
```

**Параметры:**

- `scenario_type` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ScenarioResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Scenario Endpoint

Get scenario by ID

```http
GET /user/scenarios/{scenario_id}
```

**Параметры:**

- `scenario_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ScenarioResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Execute Scenario Endpoint

Execute a scenario

```http
POST /user/scenarios/{scenario_id}/execute
```

**Параметры:**

- `scenario_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ScenarioExecute`

**Ответы:**

- `200` - Successful Response
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## CLANS Endpoints

### Get Clans Endpoint

Get clans with optional filters

```http
GET /user/clans
```

**Параметры:**

- `name` (string (optional)) - No description
- `tag` (string (optional)) - No description
- `search` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Clan Endpoint

Create a new clan

```http
POST /user/clans
```

**Параметры:**


**Тело запроса:**

Схема: `ClanCreate`

**Ответы:**

- `201` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Clan Endpoint

Delete clan (only owner)

```http
DELETE /user/clans/{clan_id}
```

**Параметры:**

- `clan_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Clan Endpoint

Get clan by ID

```http
GET /user/clans/{clan_id}
```

**Параметры:**

- `clan_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Clan Endpoint

Update clan (only owner or moderator)

```http
PUT /user/clans/{clan_id}
```

**Параметры:**

- `clan_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ClanUpdate`. Обновление инвентаря отключено: поле `inventory` в теле не принимается (422 при передаче).

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Add Clan Member Endpoint

Add member to clan (only owner or moderator)

```http
POST /user/clans/{clan_id}/members
```

**Параметры:**

- `clan_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ClanMemberAdd`

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Remove Clan Member Endpoint

Remove member from clan (выход из клана или кик). У удалённого игрока в аналитике сбрасывается привязка к клану (`clan_id`).

```http
DELETE /user/clans/{clan_id}/members/{member_id}
```

**Параметры:**

- `clan_id` (integer (required)) - No description
- `member_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Clan Member Role Endpoint

Update clan member role (only owner)

```http
PUT /user/clans/{clan_id}/members/{member_id}/role
```

**Параметры:**

- `clan_id` (integer (required)) - No description
- `member_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ClanMemberUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `ClanResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## PARTY Endpoints

### Get Parties Endpoint

Get parties

```http
GET /user/parties
```

**Параметры:**

- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Party Endpoint

Create a new party

```http
POST /user/parties
```

**Параметры:**


**Тело запроса:**

Схема: `PartyCreate`

**Ответы:**

- `201` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Party Endpoint

Delete party (only leader)

```http
DELETE /user/parties/{party_id}
```

**Параметры:**

- `party_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Party Endpoint

Get party by ID

```http
GET /user/parties/{party_id}
```

**Параметры:**

- `party_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Party Endpoint

Update party (only leader)

```http
PUT /user/parties/{party_id}
```

**Параметры:**

- `party_id` (integer (required)) - No description

**Тело запроса:**

Схема: `PartyUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Add Party Member Endpoint

Add member to party

```http
POST /user/parties/{party_id}/members
```

**Параметры:**

- `party_id` (integer (required)) - No description

**Тело запроса:**

Схема: `PartyMemberAdd`

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Remove Party Member Endpoint

Remove member from party

```http
DELETE /user/parties/{party_id}/members/{member_id}
```

**Параметры:**

- `party_id` (integer (required)) - No description
- `member_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Transfer Party Leadership Endpoint

Transfer party leadership (only current leader)

```http
POST /user/parties/{party_id}/transfer-leadership
```

**Параметры:**

- `party_id` (integer (required)) - No description
- `new_leader_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `PartyResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## MARKET Endpoints

### Get Market Items Endpoint

Get market items with optional filters

```http
GET /user/market/items
```

**Параметры:**

- `seller_id` (string (optional)) - No description
- `item_id` (string (optional)) - No description
- `search` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `MarketItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Market Item Endpoint

Create a new market item

```http
POST /user/market/items
```

**Параметры:**


**Тело запроса:**

Схема: `MarketItemCreate`

**Ответы:**

- `201` - Successful Response (Схема: `MarketItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Market Item Endpoint

Delete market item (only seller)

```http
DELETE /user/market/items/{item_id}
```

**Параметры:**

- `item_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Market Item Endpoint

Get market item by ID

```http
GET /user/market/items/{item_id}
```

**Параметры:**

- `item_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `MarketItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Market Item Endpoint

Update market item (only seller)

```http
PUT /user/market/items/{item_id}
```

**Параметры:**

- `item_id` (integer (required)) - No description

**Тело запроса:**

Схема: `MarketItemUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `MarketItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## SHOPS Endpoints

### Get Shops Endpoint

Get shops

```http
GET /user/shops
```

**Параметры:**

- `owner_id` (string (optional)) - No description
- `page` (integer (optional)) - No description
- `per_page` (integer (optional)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ShopResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Shop Endpoint

Create a new shop

```http
POST /user/shops
```

**Параметры:**


**Тело запроса:**

Схема: `ShopCreate`

**Ответы:**

- `201` - Successful Response (Схема: `ShopResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Shop Endpoint

Delete shop (only owner)

```http
DELETE /user/shops/{shop_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Shop Endpoint

Get shop by ID with items

```http
GET /user/shops/{shop_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `ShopWithItemsResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Shop Endpoint

Update shop (only owner)

```http
PUT /user/shops/{shop_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `ShopResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Shop Items Endpoint

Get shop items

```http
GET /user/shops/{shop_id}/items
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Массив: `ShopItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Shop Item Endpoint

Create shop item (only owner)

```http
POST /user/shops/{shop_id}/items
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopItemCreate`

**Ответы:**

- `201` - Successful Response (Схема: `ShopItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Full Sync Shop Items Endpoint

Full replace/sync of shop items from external source of truth (только владелец). Принимает полный список позиций магазина и приводит `ShopItem`/`Shop.inventory` в соответствие: создаёт отсутствующие, обновляет существующие (по `item_id` + `item_nbt`), удаляет позиции, которых нет в присланном списке.

```http
PUT /user/shops/{shop_id}/items/full-sync
```

**Параметры:**

- `shop_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopItemsFullSyncRequest` (`items`: массив `ShopItemCreate`)

**Ответы:**

- `200` - Successful Response (Схема: `ShopItemsFullSyncResponse`: `created`, `updated`, `deleted`, `total`, `items`)
- `400` - ValueError (Схема: `HTTPValidationError`-подобная ошибка от менеджера)
- `403` - Only owner can sync items
- `404` - Shop not found
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Buy Shop Item Endpoint

Buy item from shop (checks balance, transfers money to owner, decreases quantity). Логируется транзакция покупки. Подробнее см. [docs/SHOPS.md](docs/SHOPS.md).

```http
POST /user/shops/{shop_id}/items/{item_id}/buy
```

**Параметры:**

- `shop_id` (integer (required)) - No description
- `item_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopItemBuy` (`quantity`, default: `1`)

**Ответы:**

- `200` - Successful Response (Схема: `ShopPurchaseResponse`: `shop_item_id`, `item_id`, `quantity`, `total_paid`, `remaining_total_count`)
- `400` - Quantity must be at least 1 / Insufficient quantity / other ValueError
- `402` - Insufficient balance
- `404` - Shop item not found
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Delete Shop Item Endpoint

Delete shop item (only owner)

```http
DELETE /user/shops/{shop_id}/items/{item_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description
- `item_id` (integer (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Shop Item Endpoint

Update shop item (only owner). Можно обновить цену, размер лота, остаток (`total_count`) и NBT предмета (`item_nbt`). Остаток допускается задавать любым значением (в т.ч. увеличивать).

```http
PUT /user/shops/{shop_id}/items/{item_id}
```

**Параметры:**

- `shop_id` (integer (required)) - No description
- `item_id` (integer (required)) - No description

**Тело запроса:**

Схема: `ShopItemUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `ShopItemResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

## PROFILE Endpoints

### Get Analytics Endpoint

Get player analytics

```http
GET /user/analytics
```

**Параметры:**


**Ответы:**

- `200` - Successful Response (Схема: `PlayerAnalyticsResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Analytics Endpoint

Update player analytics

```http
PUT /user/analytics
```

**Параметры:**


**Тело запроса:**

Схема: `PlayerAnalyticsUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `PlayerAnalyticsResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Add Social Link Endpoint

Add social link to player analytics

```http
POST /user/analytics/socials
```

**Параметры:**


**Тело запроса:**

Схема: `SocialLinkAdd`

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Remove Social Link Endpoint

Remove social link from player analytics

```http
DELETE /user/analytics/socials/{social_name}
```

**Параметры:**

- `social_name` (string (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `SuccessResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Profile by Nickname Endpoint

Get player profile by nickname. Аутентификация не требуется. Если игрок существует, но у него ещё нет профиля, профиль (и analytics) создаются автоматически, чтобы эндпоинт вернул `200` вместо `404`.

```http
GET /user/profile/by-nickname/{nickname}
```

**Параметры:**

- `nickname` (string (required)) - No description

**Ответы:**

- `200` - Successful Response (Схема: `PlayerProfileResponse`)
- `404` - Player not found
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get Profile Endpoint

Get player profile

```http
GET /user/profile
```

**Параметры:**


**Ответы:**

- `200` - Successful Response (Схема: `PlayerProfileResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Create Profile Endpoint

Create player profile

```http
POST /user/profile
```

**Параметры:**


**Тело запроса:**

Схема: `PlayerProfileUpdate`

**Ответы:**

- `201` - Successful Response (Схема: `PlayerProfileResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Update Profile Endpoint

Update player profile

```http
PUT /user/profile
```

**Параметры:**


**Тело запроса:**

Схема: `PlayerProfileUpdate`

**Ответы:**

- `200` - Successful Response (Схема: `PlayerProfileResponse`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Get My Sessions Endpoint

Get current player's play sessions (no admin required).

```http
GET /user/sessions
```

**Параметры:**

- `start_date` (datetime (optional)) - No description
- `end_date` (datetime (optional)) - No description
- `limit` (integer (optional), default: `50`, 1–200) - No description

**Ответы:**

- `200` - Successful Response (массив объектов сессий: `id`, `player_id`, `start_time`, `end_time`, `duration_seconds`)
- `422` - Validation Error (Схема: `HTTPValidationError`)

---

### Link Telegram Endpoint

Привязать Telegram-аккаунт к текущему игроку. Один `tg_id` не может быть привязан к разным игрокам.

```http
POST /user/profile/telegram/link
```

**Тело запроса:** Схема: `TelegramLinkRequest` (`tg_id`: int). **Ответы:** `200` (SuccessResponse), `400`, `409` (Telegram уже привязан к другому аккаунту), `422`.

---


## Схемы данных

Всего схем: 92

- `AdminActionLogResponse`
- `AnnouncementCreate`
- `AnnouncementResponse`
- `AnnouncementUpdate`
- `BalanceResponse`
- `BanCreate`
- `BanResponse`
- `DailyRewardResponse`
- `BotSettingsResponse`
- `BotSettingsUpdate`
- `ClanCreate`
- `ClanMemberAdd`
- `ClanMemberUpdate`
- `ClanResponse`
- `ClanRole`
- `ClanUpdate`
- `CraftResponse`
- `EraStamp`
- `FriendRequest`
- `FriendResponse`
- `HTTPValidationError`
- `IdentityResponse`
- `MarketItemCreate`
- `MarketItemResponse`
- `MarketItemUpdate`
- `MuteCreate`
- `MuteResponse`
- `MutualFriendsResponse`
- `NickChangeRequestCreate`
- `NickChangeRequestResponse`
- `NPCResponse`
- `NotificationBulkCreate`
- `NotificationResponse`
- `NotificationType`
- `PartyCreate`
- `PartyMemberAdd`
- `PartyResponse`
- `PartyUpdate`
- `PlayerAnalyticsResponse`
- `PlayerAnalyticsUpdate`
- `PlayerProfileResponse`
- `PlayerProfileUpdate`
- `PlayerQuestApplicationCreate`
- `PlayerQuestApplicationResponse`
- `PlayerQuestCreate`
- `PlayerQuestReviewRequest`
- `PlayerQuestResponse`
- `PlayerQuestSubmissionRequest`
- `PlayerSearchResult`
- `PlayerSessionCreate`
- `PlayerGender`
- `PlayerRoles`
- `PlayerWorldRating`
 - `PlaytimeRewardBatch`
 - `PlaytimeRewardEntry`
 - `PlaytimeRewardRecord`
- `QuestProgressResponse`
- `QuestResponse`
- `QuestType`
- `RankingBalanceEntry`
- `RankingOnlineTimeEntry`
- `ReferralCodeResponse`
- `ReferralJoinRequest`
- `ReferralStatsResponse`
- `ScenarioExecute`
- `ScenarioResponse`
- `ScenarioType`
- `ShopCreate`
- `ShopItemCreate`
- `ShopItemResponse`
- `ShopItemUpdate`
- `ShopResponse`
- `ShopUpdate`
- `ShopWithItemsResponse`
- `SocialLinkAdd`
- `SuccessResponse`
- `TargetAudience`
- `TelegramLinkRequest`
- `TransactionCreate`
- `TransactionResponse`
- `TransactionType`
- `TransferCreate`
- `TransferResponse`
- `ValidationError`
- `VoteCastRequest`
- `VoteCreate`
- `VoteOptionCreate`
- `VoteOptionResponse`
- `VoteResponse`
- `VoteStatsResponse`
- `WalletFreezeRequest`
- `WalletUnfreezeRequest`
- `WarnCreate`
- `WarnResponse`
