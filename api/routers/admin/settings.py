"""
Admin bot settings router: GET/PUT all settings, optional GET/PUT by key.
"""

from fastapi import APIRouter, HTTPException, Depends
from core.models.players.players import Player
from core.managers.safety.settings import (
    get_all_settings,
    get_setting,
    set_setting,
    set_settings,
)
from api.schemas.admin import BotSettingsResponse, BotSettingsUpdate
from api.dependencies import get_current_admin
from core.shared.logger import logger

router = APIRouter(prefix="/admin", tags=["admin", "settings"])


@router.get("/settings", response_model=BotSettingsResponse)
async def get_settings_endpoint(admin: Player = Depends(get_current_admin)):
    """Get all bot settings. Admin/Owner only."""
    try:
        settings = await get_all_settings()
        return BotSettingsResponse(settings=settings)
    except Exception as e:
        logger.error("Failed to get settings via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", response_model=BotSettingsResponse)
async def put_settings_endpoint(
    body: BotSettingsUpdate, admin: Player = Depends(get_current_admin)
):
    """Update bot settings (merge with existing). Admin/Owner only."""
    try:
        if body.settings:
            await set_settings(body.settings)
        settings = await get_all_settings()
        return BotSettingsResponse(settings=settings)
    except Exception as e:
        logger.error("Failed to update settings via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/{key}")
async def get_setting_by_key_endpoint(
    key: str, admin: Player = Depends(get_current_admin)
):
    """Get one setting by key. Admin/Owner only."""
    try:
        value = await get_setting(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Setting not found")
        return {"key": key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get setting via API", error=str(e), key=key)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/{key}")
async def put_setting_by_key_endpoint(
    key: str,
    body: dict,
    admin: Player = Depends(get_current_admin),
):
    """Update one setting. Body: { \"value\": \"...\" }. Admin/Owner only."""
    try:
        value = body.get("value")
        if value is None:
            raise HTTPException(status_code=400, detail="value is required")
        await set_setting(key, str(value))
        return {"key": key, "value": str(value)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update setting via API", error=str(e), key=key)
        raise HTTPException(status_code=500, detail=str(e))
