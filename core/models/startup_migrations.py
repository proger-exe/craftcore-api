from pathlib import Path

from tortoise import connections

from core.shared.logger import logger


MIGRATION_NAME = "shop_inventory_migration_v2"
MIGRATION_FILE = Path(__file__).resolve().parents[2] / "shop_inventory_migration.sql"


async def run_startup_migrations() -> None:
    """
    Run SQL startup migrations once per database.
    Uses a DB marker table to guarantee one-time execution.
    """
    conn = connections.get("default")

    await conn.execute_script(
        """
        CREATE TABLE IF NOT EXISTS startup_migrations (
            name TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    applied = await conn.execute_query_dict(
        "SELECT name FROM startup_migrations WHERE name = $1 LIMIT 1;",
        [MIGRATION_NAME],
    )
    if applied:
        logger.info("Startup migration already applied", migration=MIGRATION_NAME)
    else:
        if not MIGRATION_FILE.exists():
            logger.warning(
                "Startup migration SQL file not found",
                migration=MIGRATION_NAME,
                path=str(MIGRATION_FILE),
            )
        else:
            sql = MIGRATION_FILE.read_text(encoding="utf-8")
            await conn.execute_script(sql)
            await conn.execute_query(
                "INSERT INTO startup_migrations(name) VALUES ($1);",
                [MIGRATION_NAME],
            )
            logger.info("Startup migration applied", migration=MIGRATION_NAME)

    # Player frozen_balance column (wallet freeze) — always check so it runs
    # even when shop_inventory_migration_v2 was already applied earlier.
    frozen_name = "player_frozen_balance_v1"
    applied_frozen = await conn.execute_query_dict(
        "SELECT name FROM startup_migrations WHERE name = $1 LIMIT 1;",
        [frozen_name],
    )
    if not applied_frozen:
        await conn.execute_script(
            "ALTER TABLE player ADD COLUMN IF NOT EXISTS frozen_balance INT NOT NULL DEFAULT 0;"
        )
        await conn.execute_query(
            "INSERT INTO startup_migrations(name) VALUES ($1);",
            [frozen_name],
        )
        logger.info("Startup migration applied", migration=frozen_name)

    # System owner: player id 777000 as OWNER (create if missing)
    owner_migration_name = "player_777000_owner_v1"
    applied_owner = await conn.execute_query_dict(
        "SELECT name FROM startup_migrations WHERE name = $1 LIMIT 1;",
        [owner_migration_name],
    )
    if not applied_owner:
        await conn.execute_script(
            """
            INSERT INTO player (id, role, balance, frozen_balance, language, has_locked, has_banned)
            VALUES (777000, 'owner', 0, 0, 'ru', false, false)
            ON CONFLICT (id) DO UPDATE SET role = 'owner';
            """
        )
        await conn.execute_query(
            "INSERT INTO startup_migrations(name) VALUES ($1);",
            [owner_migration_name],
        )
        logger.info("Startup migration applied", migration=owner_migration_name)

    # PlayerAnalytics daily streak and last_daily_reward_at columns
    daily_migration_name = "player_daily_streak_v1"
    applied_daily = await conn.execute_query_dict(
        "SELECT name FROM startup_migrations WHERE name = $1 LIMIT 1;",
        [daily_migration_name],
    )
    if not applied_daily:
        await conn.execute_script(
            """
            ALTER TABLE player_analytics
            ADD COLUMN IF NOT EXISTS daily_streak_days INT NOT NULL DEFAULT 0;
            ALTER TABLE player_analytics
            ADD COLUMN IF NOT EXISTS daily_streak_max INT NOT NULL DEFAULT 0;
            ALTER TABLE player_analytics
            ADD COLUMN IF NOT EXISTS last_daily_reward_at TIMESTAMPTZ NULL;
            """
        )
        await conn.execute_query(
            "INSERT INTO startup_migrations(name) VALUES ($1);",
            [daily_migration_name],
        )
        logger.info("Startup migration applied", migration=daily_migration_name)

    # ShopItem item_nbt column and unique (shop_id, item_id, item_nbt)
    shop_nbt_migration_name = "shop_items_item_nbt_v1"
    applied_shop_nbt = await conn.execute_query_dict(
        "SELECT name FROM startup_migrations WHERE name = $1 LIMIT 1;",
        [shop_nbt_migration_name],
    )
    if not applied_shop_nbt:
        await conn.execute_script(
            """
            ALTER TABLE shop_items
            ADD COLUMN IF NOT EXISTS item_nbt TEXT NOT NULL DEFAULT '';
            """
        )
        await conn.execute_script(
            """
            ALTER TABLE shop_items
            DROP CONSTRAINT IF EXISTS shop_items_shop_id_item_id_key;
            """
        )
        await conn.execute_script(
            """
            ALTER TABLE shop_items
            ADD CONSTRAINT shop_items_shop_id_item_id_item_nbt_key
            UNIQUE (shop_id, item_id, item_nbt);
            """
        )
        await conn.execute_query(
            "INSERT INTO startup_migrations(name) VALUES ($1);",
            [shop_nbt_migration_name],
        )
        logger.info("Startup migration applied", migration=shop_nbt_migration_name)

    player_quest_marketplace_name = "player_quest_marketplace_v1"
    applied_player_quest_marketplace = await conn.execute_query_dict(
        "SELECT name FROM startup_migrations WHERE name = $1 LIMIT 1;",
        [player_quest_marketplace_name],
    )
    if not applied_player_quest_marketplace:
        has_player_quests = await conn.execute_query_dict(
            "SELECT to_regclass('public.player_quests') AS table_name"
        )
        if has_player_quests and has_player_quests[0]["table_name"]:
            await conn.execute_script(
                """
                ALTER TABLE player_quests
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

                ALTER TABLE player_quests
                ALTER COLUMN status TYPE VARCHAR(32);

                UPDATE player_quests
                SET status = 'open'
                WHERE status = 'active';

                UPDATE player_quests
                SET status = 'in_progress'
                WHERE status = 'open' AND executor_id IS NOT NULL;

                CREATE TABLE IF NOT EXISTS player_quest_applications (
                    id BIGSERIAL PRIMARY KEY,
                    quest_id BIGINT NOT NULL REFERENCES player_quests(id) ON DELETE CASCADE,
                    applicant_id BIGINT NOT NULL REFERENCES player(id) ON DELETE CASCADE,
                    status VARCHAR(32) NOT NULL DEFAULT 'applied',
                    cover_letter TEXT NULL,
                    submission_message TEXT NULL,
                    review_comment TEXT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_player_quests_status
                ON player_quests(status);

                CREATE INDEX IF NOT EXISTS idx_player_quests_creator_status
                ON player_quests(creator_id, status);

                CREATE INDEX IF NOT EXISTS idx_player_quest_applications_quest_status
                ON player_quest_applications(quest_id, status);

                CREATE INDEX IF NOT EXISTS idx_player_quest_applications_applicant_status
                ON player_quest_applications(applicant_id, status);
                """
            )

            # Legacy active quests used direct balance deduction. Close them and refund once.
            active_quests = await conn.execute_query_dict(
                """
                SELECT id, creator_id, reward
                FROM player_quests
                WHERE status IN ('open', 'in_progress')
                """
            )
            for quest in active_quests:
                await conn.execute_query(
                    """
                    UPDATE player
                    SET balance = balance + $1
                    WHERE id = $2
                    """,
                    [quest["reward"], quest["creator_id"]],
                )
            await conn.execute_query(
                """
                UPDATE player_quests
                SET status = 'cancelled', executor_id = NULL, updated_at = NOW()
                WHERE status IN ('open', 'in_progress')
                """
            )

        await conn.execute_query(
            "INSERT INTO startup_migrations(name) VALUES ($1);",
            [player_quest_marketplace_name],
        )
        logger.info(
            "Startup migration applied", migration=player_quest_marketplace_name
        )
