"""User nick change: request, history."""

from fastapi import APIRouter, HTTPException, Depends
from core.models.players.players import Player
from core.managers.safety.nickchange import (
    create_nick_change_request,
    get_player_nick_history,
)
from api.schemas.nickchange import NickChangeRequestCreate, NickChangeRequestResponse
from api.dependencies import get_current_player
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "nickchange"])


@router.post("/nickchange/request", response_model=NickChangeRequestResponse)
async def create_nick_change_request_endpoint(
    body: NickChangeRequestCreate,
    player: Player = Depends(get_current_player),
):
    """Submit a nick change request."""
    try:
        req = await create_nick_change_request(player, body.new_nick)
        return NickChangeRequestResponse(
            id=req.id,
            player_id=req.player_id,
            new_nick=req.new_nick,
            status=req.status,
            created_at=req.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create nick change request via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nickchange/history")
async def get_nick_change_history_endpoint(
    player: Player = Depends(get_current_player),
):
    """Get my nick change history."""
    try:
        history = await get_player_nick_history(player.id)
        return {"history": history}
    except Exception as e:
        logger.error("Failed to get nick history via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
