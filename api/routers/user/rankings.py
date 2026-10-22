"""
User rankings: top by balance, top by online time.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from core.models.players.players import Player
from core.managers.economics.transactions import get_top_players_by_balance
from core.shared.analytics import get_top_players_by_online_time
from api.schemas.admin import RankingBalanceEntry, RankingOnlineTimeEntry
from api.dependencies import get_current_player
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "rankings"])


@router.get("/rankings/balance", response_model=list[RankingBalanceEntry])
async def get_rankings_balance_endpoint(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    player: Player = Depends(get_current_player),
):
    """Top players by balance."""
    try:
        top = await get_top_players_by_balance(limit=limit + offset)
        slice_top = top[offset : offset + limit]
        return [
            RankingBalanceEntry(
                player_id=p.id,
                nickname=p.nickname,
                balance=p.balance,
                rank=offset + i + 1,
            )
            for i, p in enumerate(slice_top)
        ]
    except Exception as e:
        logger.error("Failed to get balance rankings via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/online-time", response_model=list[RankingOnlineTimeEntry])
async def get_rankings_online_time_endpoint(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    player: Player = Depends(get_current_player),
):
    """Top players by total online time (seconds)."""
    try:
        entries = await get_top_players_by_online_time(limit=limit, offset=offset)
        return [RankingOnlineTimeEntry(**e) for e in entries]
    except Exception as e:
        logger.error("Failed to get online-time rankings via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
