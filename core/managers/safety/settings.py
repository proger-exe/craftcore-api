"""
Bot settings manager: get/set key-value settings.
"""

from typing import Dict, Optional
from core.models.safety.settings import BotSettings
from core.shared.logger import logger


async def get_all_settings() -> Dict[str, str]:
    """Return all settings as key -> value."""
    try:
        rows = await BotSettings.all().values_list("key", "value")
        return dict(rows)
    except Exception as e:
        logger.error("Failed to get all settings", error=str(e))
        raise


async def get_setting(key: str) -> Optional[str]:
    """Return value for key or None."""
    try:
        row = await BotSettings.get_or_none(key=key)
        return row.value if row else None
    except Exception as e:
        logger.error("Failed to get setting", error=str(e), key=key)
        raise


async def set_setting(key: str, value: str) -> None:
    """Set or update one setting."""
    try:
        await BotSettings.update_or_create(
            {"value": value},
            key=key,
        )
        logger.info("Bot setting updated", key=key)
    except Exception as e:
        logger.error("Failed to set setting", error=str(e), key=key)
        raise


async def set_settings(settings: Dict[str, str]) -> None:
    """Set multiple settings."""
    try:
        for key, value in settings.items():
            await BotSettings.update_or_create(
                {"value": value},
                key=key,
            )
        logger.info("Bot settings updated", count=len(settings))
    except Exception as e:
        logger.error("Failed to set settings", error=str(e))
        raise
