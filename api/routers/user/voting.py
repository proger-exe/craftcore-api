"""
User voting: list votes, get vote, cast vote, get stats.
"""

from fastapi import APIRouter, HTTPException, Depends
from core.models.players.players import Player
from core.managers.mailing.voting import (
    get_vote,
    list_votes_active,
    cast_vote,
    get_vote_stats,
)
from api.schemas.voting import (
    VoteResponse,
    VoteOptionResponse,
    VoteCastRequest,
    VoteStatsResponse,
)
from api.dependencies import get_current_player
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "voting"])


def _vote_to_response(vote, stats=None):
    if stats is None:
        stats = get_vote_stats(vote)
    opts = [
        VoteOptionResponse(
            id=o["id"], text=o["text"], votes=o["votes"], percentage=o.get("percentage")
        )
        for o in stats["options"]
    ]
    cby_id = getattr(vote, "created_by_id", None)
    return VoteResponse(
        id=vote.id,
        created_by_id=cby_id,
        title=vote.title,
        description=vote.description,
        options=opts,
        total_votes=stats["total_votes"],
        created_at=vote.created_at,
        ends_at=vote.ends_at,
    )


@router.get("/votes", response_model=list[VoteResponse])
async def list_votes_endpoint(
    limit: int = 50,
    player: Player = Depends(get_current_player),
):
    """List active votes."""
    try:
        votes = await list_votes_active(limit=limit)
        return [_vote_to_response(v) for v in votes]
    except Exception as e:
        logger.error("Failed to list votes via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/votes/{vote_id}", response_model=VoteResponse)
async def get_vote_endpoint(
    vote_id: int,
    player: Player = Depends(get_current_player),
):
    """Get vote by id with current stats."""
    try:
        vote = await get_vote(vote_id)
        if not vote:
            raise HTTPException(status_code=404, detail="Vote not found")
        return _vote_to_response(vote)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get vote via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/votes/{vote_id}/vote", response_model=VoteResponse)
async def cast_vote_endpoint(
    vote_id: int,
    body: VoteCastRequest,
    player: Player = Depends(get_current_player),
):
    """Cast vote. Requires at least 1 hour playtime."""
    try:
        vote = await get_vote(vote_id)
        if not vote:
            raise HTTPException(status_code=404, detail="Vote not found")
        updated = await cast_vote(vote, player, body.option_id)
        return _vote_to_response(updated)
    except ValueError as e:
        err = str(e)
        if "1 hour" in err:
            raise HTTPException(status_code=403, detail=err)
        if "Already voted" in err:
            raise HTTPException(status_code=409, detail=err)
        if "Invalid option" in err:
            raise HTTPException(status_code=400, detail=err)
        raise HTTPException(status_code=400, detail=err)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cast vote via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/votes/{vote_id}/stats", response_model=VoteStatsResponse)
async def get_vote_stats_endpoint(
    vote_id: int,
    player: Player = Depends(get_current_player),
):
    """Get vote statistics (counts and percentages)."""
    try:
        vote = await get_vote(vote_id)
        if not vote:
            raise HTTPException(status_code=404, detail="Vote not found")
        stats = get_vote_stats(vote)
        return VoteStatsResponse(
            total_votes=stats["total_votes"],
            options=[
                VoteOptionResponse(
                    id=o["id"],
                    text=o["text"],
                    votes=o["votes"],
                    percentage=o.get("percentage"),
                )
                for o in stats["options"]
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get vote stats via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
