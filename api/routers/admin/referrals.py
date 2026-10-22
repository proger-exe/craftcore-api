"""Admin referral stats."""

from fastapi import APIRouter, Depends, HTTPException
from core.models.players.players import Player
from core.managers.social.referrals import get_all_referral_stats
from api.dependencies import get_current_admin
from core.shared.logger import logger

router = APIRouter(prefix="/admin", tags=["admin", "referrals"])


@router.get("/referrals/stats")
async def get_all_referrals_stats_endpoint(admin: Player = Depends(get_current_admin)):
    """Get aggregate referral stats. Admin only."""
    try:
        return await get_all_referral_stats()
    except Exception as e:
        logger.error("Failed to get referral stats via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
