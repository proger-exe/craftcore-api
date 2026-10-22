"""
Nick change requests: create, list, approve, reject, history.
"""

import re
from typing import List, Optional

from tortoise.transactions import in_transaction

from core.models.safety.nickchange import NickChangeRequest
from core.models.players.players import Player
from core.managers.players.players import get_player_by_nickname, update_player
from core.shared.logger import logger

NICK_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


def validate_nick(nick: str) -> None:
    if not nick or not NICK_PATTERN.match(nick):
        raise ValueError(
            "Invalid nick format: 3-32 chars, letters, digits, underscore only"
        )


async def create_nick_change_request(
    player: Player, new_nick: str
) -> NickChangeRequest:
    validate_nick(new_nick)
    existing = await get_player_by_nickname(new_nick)
    if existing and existing.id != player.id:
        raise ValueError("Nick already taken")
    req = await NickChangeRequest.create(
        player=player,
        new_nick=new_nick,
        status="pending",
        history=[],
    )
    logger.info("Nick change requested", player_id=player.id, new_nick=new_nick)
    return req


async def list_nick_change_requests(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[NickChangeRequest]:
    qs = (
        NickChangeRequest.all()
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
        .prefetch_related("player")
    )
    if status:
        qs = qs.filter(status=status)
    return await qs


async def approve_nick_change_request(request_id: int) -> NickChangeRequest:
    async with in_transaction() as conn:
        req = (
            await NickChangeRequest.filter(id=request_id)
            .using_db(conn)
            .select_for_update()
            .first()
        )
        if not req:
            raise ValueError("Request not found")
        if req.status != "pending":
            raise ValueError("Request is not pending")

        await req.fetch_related("player")
        player = req.player
        old_nick = player.nickname
        await update_player(player, nickname=req.new_nick)

        history = list(req.history or [])
        history.append(
            {
                "old_nick": old_nick,
                "new_nick": req.new_nick,
                "changed_at": req.created_at.isoformat() if req.created_at else None,
            }
        )
        req.status = "approved"
        req.history = history
        await req.save(update_fields=["status", "history"], using_db=conn)
    logger.info("Nick change approved", request_id=request_id, new_nick=req.new_nick)
    return req


async def reject_nick_change_request(request_id: int) -> NickChangeRequest:
    req = await NickChangeRequest.get_or_none(id=request_id)
    if not req:
        raise ValueError("Request not found")
    if req.status != "pending":
        raise ValueError("Request is not pending")
    req.status = "rejected"
    await req.save(update_fields=["status"])
    return req


async def get_player_nick_history(player_id: int) -> List[dict]:
    """History entries from approved requests (from history JSON)."""
    reqs = await NickChangeRequest.filter(
        player_id=player_id, status="approved"
    ).order_by("-created_at")
    out = []
    for req in reqs:
        for h in req.history or []:
            if isinstance(h, dict):
                out.append(h)
    return out
