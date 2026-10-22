"""Admin nick change: list requests, approve, reject."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from core.managers.safety.nickchange import (
    list_nick_change_requests,
    approve_nick_change_request,
    reject_nick_change_request,
)
from api.schemas.nickchange import NickChangeRequestResponse
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_moderator
from core.models.players.players import Player
from core.shared.logger import logger

router = APIRouter(prefix="/admin", tags=["admin", "nickchange"])


@router.get("/nickchange/requests", response_model=list[NickChangeRequestResponse])
async def list_nick_change_requests_endpoint(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: Player = Depends(get_current_moderator),
):
    """List nick change requests."""
    try:
        reqs = await list_nick_change_requests(
            status=status, limit=limit, offset=offset
        )
        return [
            NickChangeRequestResponse(
                id=r.id,
                player_id=r.player_id,
                new_nick=r.new_nick,
                status=r.status,
                created_at=r.created_at,
            )
            for r in reqs
        ]
    except Exception as e:
        logger.error("Failed to list nick change requests via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nickchange/{request_id}/approve", response_model=SuccessResponse)
async def approve_nick_change_endpoint(
    request_id: int,
    admin: Player = Depends(get_current_moderator),
):
    """Approve nick change request."""
    try:
        await approve_nick_change_request(request_id)
        return SuccessResponse(message="Nick change approved")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to approve nick change via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nickchange/{request_id}/reject", response_model=SuccessResponse)
async def reject_nick_change_endpoint(
    request_id: int,
    admin: Player = Depends(get_current_moderator),
):
    """Reject nick change request."""
    try:
        await reject_nick_change_request(request_id)
        return SuccessResponse(message="Nick change rejected")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to reject nick change via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
