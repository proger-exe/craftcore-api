"""
User social router for friends
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from api.schemas.social import (
    FriendRequest,
    FriendResponse,
    MutualFriendsResponse,
)
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player
from core.models.players.players import Player
from core.models.social.friends import FriendStatus
from core.managers.social.friends import (
    send_friend_request,
    get_player_friends,
    get_friend_requests,
    accept_friend_request,
    reject_friend_request,
    remove_friend,
    block_friend,
    unblock_friend,
    get_friend_relationship,
    get_mutual_friends,
    get_friend_suggestions,
)
from core.managers.players.players import get_player as get_player_by_id
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "social"])


def _friend_to_response(friend_rel) -> FriendResponse:
    """Build FriendResponse from Friend model (after fetch_related)."""
    return FriendResponse(
        id=friend_rel.id,
        player_id=(
            friend_rel.player.id
            if hasattr(friend_rel.player, "id")
            else getattr(friend_rel, "player_id", 0)
        ),
        friend_id=(
            friend_rel.friend.id
            if hasattr(friend_rel.friend, "id")
            else getattr(friend_rel, "friend_id", 0)
        ),
        status=(
            friend_rel.status.value
            if hasattr(friend_rel.status, "value")
            else str(friend_rel.status)
        ),
        requested_at=friend_rel.requested_at,
        accepted_at=friend_rel.accepted_at,
        created_at=friend_rel.created_at,
        updated_at=friend_rel.updated_at,
    )


@router.post("/friends/request", response_model=FriendResponse, status_code=201)
async def send_friend_request_endpoint(
    request_data: FriendRequest, player: Player = Depends(get_current_player)
):
    """Send friend request"""
    try:
        friend = await get_player_by_id(request_data.friend_id)
        if not friend:
            raise HTTPException(status_code=404, detail="Friend player not found")

        friend_rel = await send_friend_request(player=player, friend=friend)
        await friend_rel.fetch_related("player", "friend")
        return _friend_to_response(friend_rel)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send friend request via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friends", response_model=List[FriendResponse])
async def get_friends_endpoint(
    player: Player = Depends(get_current_player),
):
    """Get player's friends"""
    try:
        friends = await get_player_friends(player, status=FriendStatus.ACCEPTED)
        for f in friends:
            await f.fetch_related("player", "friend")
        return [_friend_to_response(f) for f in friends]
    except Exception as e:
        logger.error("Failed to get friends via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friends/requests", response_model=List[FriendResponse])
async def get_friend_requests_endpoint(
    incoming: bool = Query(True),
    player: Player = Depends(get_current_player),
):
    """Get friend requests (incoming or outgoing)"""
    try:
        requests = await get_friend_requests(player, incoming=incoming)
        for r in requests:
            await r.fetch_related("player", "friend")
        return [_friend_to_response(r) for r in requests]
    except Exception as e:
        logger.error("Failed to get friend requests via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/friends/{friend_id}/accept", response_model=FriendResponse)
async def accept_friend_request_endpoint(
    friend_id: int, player: Player = Depends(get_current_player)
):
    """Accept friend request"""
    try:
        friend = await get_player_by_id(friend_id)
        if not friend:
            raise HTTPException(status_code=404, detail="Friend player not found")

        # Get the friend relationship (incoming request)
        friend_rel = await get_friend_relationship(player=friend, friend=player)
        if not friend_rel:
            raise HTTPException(status_code=404, detail="Friend request not found")

        accepted = await accept_friend_request(friend_rel=friend_rel)
        await accepted.fetch_related("player", "friend")
        return _friend_to_response(accepted)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to accept friend request via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/friends/{friend_id}/reject", response_model=SuccessResponse)
async def reject_friend_request_endpoint(
    friend_id: int, player: Player = Depends(get_current_player)
):
    """Reject friend request"""
    try:
        friend = await get_player_by_id(friend_id)
        if not friend:
            raise HTTPException(status_code=404, detail="Friend player not found")

        # Get the friend relationship (incoming request)
        friend_rel = await get_friend_relationship(player=friend, friend=player)
        if not friend_rel:
            raise HTTPException(status_code=404, detail="Friend request not found")

        await reject_friend_request(friend_rel=friend_rel)
        return SuccessResponse(message="Friend request rejected")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reject friend request via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/friends/{friend_id}", response_model=SuccessResponse)
async def remove_friend_endpoint(
    friend_id: int, player: Player = Depends(get_current_player)
):
    """Remove friend"""
    try:
        friend = await get_player_by_id(friend_id)
        if not friend:
            raise HTTPException(status_code=404, detail="Friend player not found")

        await remove_friend(player=player, friend=friend)
        return SuccessResponse(message="Friend removed successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove friend via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/friends/{friend_id}/block", response_model=FriendResponse)
async def block_friend_endpoint(
    friend_id: int, player: Player = Depends(get_current_player)
):
    """Block friend"""
    try:
        friend = await get_player_by_id(friend_id)
        if not friend:
            raise HTTPException(status_code=404, detail="Friend player not found")

        blocked = await block_friend(player=player, friend=friend)
        await blocked.fetch_related("player", "friend")
        return _friend_to_response(blocked)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to block friend via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/friends/{friend_id}/unblock", response_model=SuccessResponse)
async def unblock_friend_endpoint(
    friend_id: int, player: Player = Depends(get_current_player)
):
    """Unblock friend"""
    try:
        friend = await get_player_by_id(friend_id)
        if not friend:
            raise HTTPException(status_code=404, detail="Friend player not found")

        result = await unblock_friend(player=player, friend=friend)
        if result:
            return SuccessResponse(message="Friend unblocked successfully")
        else:
            raise HTTPException(
                status_code=404, detail="Friend relationship not found or not blocked"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to unblock friend via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friends/mutual/{player_id}", response_model=MutualFriendsResponse)
async def get_mutual_friends_endpoint(
    player_id: int, player: Player = Depends(get_current_player)
):
    """Get mutual friends with another player"""
    try:
        other_player = await get_player_by_id(player_id)
        if not other_player:
            raise HTTPException(status_code=404, detail="Player not found")

        mutual = await get_mutual_friends(player1=player, player2=other_player)
        return MutualFriendsResponse(
            player1_id=player.id,
            player2_id=other_player.id,
            mutual_friends=[{"id": p.id, "nickname": p.nickname} for p in mutual],
            count=len(mutual),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get mutual friends via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friends/suggestions", response_model=List[dict])
async def get_friend_suggestions_endpoint(
    limit: int = Query(10, ge=1, le=50),
    player: Player = Depends(get_current_player),
):
    """Get friend suggestions"""
    try:
        suggestions = await get_friend_suggestions(player, limit=limit)
        return [{"id": p.id, "nickname": p.nickname} for p in suggestions]
    except Exception as e:
        logger.error("Failed to get friend suggestions via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
