# Миграции БД

Документ описывает механизм миграций и перечень всех startup-миграций в проекте.

---

## Механизм

- **Инициализация** ([core/models/__init__.py](../core/models/__init__.py)): при старте приложения вызываются по порядку `Tortoise.init()` → `run_startup_migrations()` → `Tortoise.generate_schemas(safe=True)`.
- **Startup-миграции** ([core/models/startup_migrations.py](../core/models/startup_migrations.py)): SQL выполняется при каждом старте; таблица `startup_migrations` (поля `name`, `applied_at`) хранит маркеры применённых миграций, каждая миграция выполняется один раз.
- **generate_schemas(safe=True)**: создаёт только **отсутствующие** таблицы по моделям Tortoise. **Новые колонки в уже существующих таблицах не добавляются** — для них нужна отдельная startup-миграция (ALTER TABLE ... ADD COLUMN) или ручной SQL.

В проекте не используется Aerich и нет папки с версионными миграциями — только стартовые SQL-скрипты и маркеры в БД.

---

## Перечень startup-миграций

| Маркер | Где выполняется | Что делает |
|--------|------------------|------------|
| `shop_inventory_migration_v2` | [core/models/startup_migrations.py](../core/models/startup_migrations.py), SQL из файла [shop_inventory_migration.sql](../shop_inventory_migration.sql) | Добавляет колонку `shops.inventory` (JSONB, default `{}`), колонку `shop_items.total_count` (INT, default 0), backfill `total_count` из `quantity`, заполняет зеркало `shops.inventory` из строк `shop_items`, нормализует NULL в `{}`. Подробнее: [docs/SHOP_INVENTORY_MIGRATION.md](SHOP_INVENTORY_MIGRATION.md), [docs/SHOPS.md](SHOPS.md). |
| `player_frozen_balance_v1` | В коде [core/models/startup_migrations.py](../core/models/startup_migrations.py) (блок после шоп-миграции) | `ALTER TABLE player ADD COLUMN IF NOT EXISTS frozen_balance INT NOT NULL DEFAULT 0;` — колонка для заморозки части баланса (кошелёк). |
| `player_777000_owner_v1` | В коде [core/models/startup_migrations.py](../core/models/startup_migrations.py) | Создаёт игрока с `id = 777000` и ролью `owner`, если его нет; если есть — выставляет `role = 'owner'`. Для работы от имени системы передавать в заголовке `X-Player-ID: 777000`. |

Порядок выполнения при старте: сначала проверка/применение `shop_inventory_migration_v2`, затем всегда проверка/применение `player_frozen_balance_v1` (чтобы колонка `frozen_balance` создавалась и на базах, где шоп-миграция уже была применена ранее), затем `player_777000_owner_v1`.

---

## Таблицы, изменённые миграциями

- **player** — колонка `frozen_balance` добавляется миграцией `player_frozen_balance_v1`.
- **shops** — колонка `inventory` добавляется в `shop_inventory_migration_v2`.
- **shop_items** — колонка `total_count` добавляется в `shop_inventory_migration_v2`, затем backfill из `quantity`.

Остальные таблицы создаются Tortoise при первом запуске (если их ещё нет) и в дальнейшем не меняются через startup-миграции в этом репозитории.

---

## Важно

**Добавление новых колонок в существующие таблицы:** Tortoise `generate_schemas(safe=True)` не добавляет колонки. Нужно либо завести новую startup-миграцию с `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` и уникальным маркером в `startup_migrations`, либо один раз выполнить ручной SQL на целевой БД.
