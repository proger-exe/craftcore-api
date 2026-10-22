BEGIN;

-- 1) Ensure shops.inventory exists if shops table already exists.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'shops'
    ) THEN
        ALTER TABLE shops
        ADD COLUMN IF NOT EXISTS inventory JSONB NOT NULL DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- 2) Add total_count for physical stock if table exists.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'shop_items'
    ) THEN
        ALTER TABLE shop_items
        ADD COLUMN IF NOT EXISTS total_count INT NOT NULL DEFAULT 0;
    END IF;
END $$;

-- 3) Backfill total_count from old quantity values (legacy stock source).
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'shop_items'
    ) THEN
        UPDATE shop_items
        SET total_count = quantity
        WHERE total_count = 0;
    END IF;
END $$;

-- 4) Build shops.inventory mirror from ShopItem rows.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'shop_items'
    ) AND EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'shops'
    ) AND EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'shops'
          AND column_name = 'inventory'
    ) THEN
        WITH inventory_by_shop AS (
            SELECT
                si.shop_id,
                jsonb_object_agg(
                    si.item_id,
                    jsonb_build_object(
                        'price', si.price,
                        'quantity', CASE WHEN si.quantity < 1 THEN 1 ELSE si.quantity END,
                        'total_count', si.total_count
                    )
                ) AS payload
            FROM shop_items si
            GROUP BY si.shop_id
        )
        UPDATE shops s
        SET inventory = inv.payload
        FROM inventory_by_shop inv
        WHERE s.id = inv.shop_id;
    END IF;
END $$;

-- 5) Ensure non-null inventory in all shops.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'shops'
    ) AND EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'shops'
          AND column_name = 'inventory'
    ) THEN
        UPDATE shops
        SET inventory = '{}'::jsonb
        WHERE inventory IS NULL;
    END IF;
END $$;

COMMIT;
