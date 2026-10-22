"""
Models package initialization
Initializes Tortoise ORM with PostgreSQL database connection
"""

from tortoise import Tortoise
from settings import settings
from core.shared.logger import logger
from core.models.startup_migrations import run_startup_migrations

# Import all models to ensure they are registered
from core.models.localization.locale import Message, Button, Languages
from core.models.players.players import (
    Player,
    PlayerProfile,
    PlayerAnalytics,
    PlayerRoles,
    PlayerGender,
    PlayerSource,
    EraStamp,
    PlayerWorldRating,
)
from core.models.economics.market import MarketItem
from core.models.economics.shops import Shop, ShopItem
from core.models.economics.transactions import Transaction, TransactionType
from core.models.economics.quests import Quest, QuestProgress, QuestType, QuestStatus
from core.models.economics.player_quests import PlayerQuest, PlayerQuestApplication
from core.models.social.clans import Clan, ClanRole
from core.models.social.party import Party, PartyRole
from core.models.social.friends import Friend, FriendStatus
from core.models.social.referrals import Referral
from core.models.safety.moderation import Ban, Mute, Warn, Arrest, AdminActionLog
from core.models.safety.settings import BotSettings
from core.models.safety.analytics import (
    ServerSnapshot,
    PlayerSession,
    PlaytimeRewardQueue,
)
from core.models.safety.nickchange import NickChangeRequest
from core.models.mailing.announcements import Announcement, TargetAudience
from core.models.mailing.notifications import Notification, NotificationType
from core.models.mailing.voting import Vote
from core.models.qol.crafts import Craft
from core.models.qol.npcs import NPC
from core.models.qol.scenarios import Scenario, ScenarioType


async def init():
    """
    Initialize Tortoise ORM with PostgreSQL database connection.

    This function sets up the database connection using settings from settings.py
    and generates database schema if it doesn't exist.

    Database configuration:
    - Host: settings.DB_HOST
    - User: settings.DB_USER
    - Password: settings.DB_PASS
    - Database: settings.DB_NAME

    Raises:
        Exception: If database connection fails
    """
    try:
        await Tortoise.init(
            db_url=f"postgres://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:5432/{settings.DB_NAME}",
            modules={
                "models": [
                    "core.models.localization.locale",
                    "core.models.players.players",
                    "core.models.economics.market",
                    "core.models.economics.shops",
                    "core.models.economics.transactions",
                    "core.models.economics.quests",
                    "core.models.economics.player_quests",
                    "core.models.social.clans",
                    "core.models.social.party",
                    "core.models.social.friends",
                    "core.models.social.referrals",
                    "core.models.safety.moderation",
                    "core.models.safety.settings",
                    "core.models.safety.analytics",
                    "core.models.safety.nickchange",
                    "core.models.mailing.announcements",
                    "core.models.mailing.notifications",
                    "core.models.mailing.voting",
                    "core.models.qol.crafts",
                    "core.models.qol.npcs",
                    "core.models.qol.scenarios",
                ]
            },
        )

        # Run SQL startup migrations before schema generation so legacy DBs
        # receive required columns (e.g. shop_items.total_count) in time.
        await run_startup_migrations()

        # Generate database schema
        await Tortoise.generate_schemas(safe=True)

        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close():
    """
    Close database connections.

    Should be called on application shutdown to properly close all database connections.
    """
    await Tortoise.close_connections()
    logger.info("Database connections closed")
