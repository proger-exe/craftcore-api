"""
Admin voting: create vote.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from core.models.players.players import Player
from core.managers.mailing.voting import create_vote, get_vote_stats
from api.schemas.voting import VoteCreate, VoteResponse, VoteOptionResponse
from api.dependencies import get_current_admin
from core.shared.logger import logger

router = APIRouter(prefix="/admin", tags=["admin", "voting"])


def _vote_to_response(vote, stats=None):
    if stats is None:
        stats = get_vote_stats(vote)
    opts = [
        VoteOptionResponse(
            id=o["id"], text=o["text"], votes=o["votes"], percentage=o.get("percentage")
        )
        for o in stats["options"]
    ]
    return VoteResponse(
        id=vote.id,
        created_by_id=vote.created_by_id if vote.created_by_id else None,
        title=vote.title,
        description=vote.description,
        options=opts,
        total_votes=stats["total_votes"],
        created_at=vote.created_at,
        ends_at=vote.ends_at,
    )


@router.post("/votes", response_model=VoteResponse, status_code=201)
async def create_vote_endpoint(
    body: VoteCreate,
    admin: Player = Depends(get_current_admin),
):
    """Create a new vote. Admin only."""
    try:
        options_dicts = [{"id": o.id, "text": o.text} for o in body.options]
        vote = await create_vote(
            created_by=admin,
            title=body.title,
            description=body.description,
            options=options_dicts,
            ends_at=body.ends_at,
        )
        stats = get_vote_stats(vote)
        return _vote_to_response(vote, stats)
    except Exception as e:
        logger.error("Failed to create vote via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
