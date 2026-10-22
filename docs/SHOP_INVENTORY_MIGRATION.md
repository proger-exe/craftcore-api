# Миграция шопов на total_count + inventory

## Что меняется

- В `shop_items` добавляется поле `total_count` (общий физический остаток товара в магазине).
- `shops.inventory` заполняется зеркалом данных из `shop_items` по схеме:
  - `price` — цена за единицу.
  - `quantity` — размер лота.
  - `total_count` — общий текущий остаток.

## Перед запуском

Сделайте бэкап таблиц:

```sql
CREATE TABLE shops_backup_20260202 AS TABLE shops;
CREATE TABLE shop_items_backup_20260202 AS TABLE shop_items;
```

## Применение

Выполните SQL-скрипт:

`shop_inventory_migration.sql`

Пример для PostgreSQL:

```bash
psql "$DATABASE_URL" -f /path/to/craftcore-global-api/shop_inventory_migration.sql
```

## Проверка после миграции

1. Проверить, что колонка есть:
```sql
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'shop_items' AND column_name = 'total_count';
```
2. Проверить заполнение:
```sql
SELECT id, item_id, quantity, total_count
FROM shop_items
ORDER BY id DESC
LIMIT 20;
```
3. Проверить зеркало inventory:
```sql
SELECT id, inventory
FROM shops
ORDER BY id DESC
LIMIT 20;
```

## Примечание

После миграции запись товара не удаляется при `total_count = 0` — это важно для сохранения параметров лота и цены без пересоздания позиции.
