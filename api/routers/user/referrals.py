"""User referral endpoints."""

from fastapi import APIRouter, Depends
from core.models.players.players import Player
from core.managers.social.referrals import (
    get_or_create_referral_code,
    join_referral,
    get_referral_stats,
)
from api.schemas.referrals import (
    ReferralCodeResponse,
    ReferralJoinRequest,
    ReferralStatsResponse,
)
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player

router = APIRouter(prefix="/user", tags=["user", "referrals"])


@router.get("/referrals/code", response_model=ReferralCodeResponse)
async def get_referral_code_endpoint(player: Player = Depends(get_current_player)):
    """Get or create my referral code."""
    ref = await get_or_create_referral_code(player)
    return ReferralCodeResponse(
        code=ref.code,
        referrals_count=len(ref.joins or []),
    )


@router.post("/referrals/join", response_model=SuccessResponse)
async def join_referral_endpoint(
    body: ReferralJoinRequest,
    player: Player = Depends(get_current_player),
):
    """Join using a referral code."""
    await join_referral(player, body.code)
    return SuccessResponse(message="Referral joined successfully")


@router.get("/referrals/stats", response_model=ReferralStatsResponse)
async def get_referral_stats_endpoint(player: Player = Depends(get_current_player)):
    """Get my referral stats."""
    stats = await get_referral_stats(player)
    return ReferralStatsResponse(**stats)
