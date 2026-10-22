"""
User party router
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from api.schemas.party import PartyCreate, PartyResponse, PartyUpdate, PartyMemberAdd
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player, validate_pagination
from core.models.players.players import Player
from core.managers.social.party import (
    create_party,
    get_party,
    get_parties,
    update_party,
    delete_party,
    add_party_member,
    remove_party_member,
    change_party_leader,
)
from core.managers.players.players import get_player as get_player_by_id
from core.managers.players.profile import (
    get_player_analytics,
    create_player_analytics,
    update_player_analytics,
)
from core.shared.errors import ForbiddenError, NotFoundError

router = APIRouter(prefix="/user", tags=["user", "party"])


def _party_leader_id(party) -> int:
    """Достать leader_id из Party (Tortoise FK может вернуть объект)."""
    o = getattr(party, "leader_id", None)
    if isinstance(o, int):
        return int(o)
    if hasattr(o, "id") and type(o).__name__ != "QuerySet":
        return int(o.id)
    raw = getattr(party, "__dict__", {}).get("leader_id")
    return int(raw) if raw is not None else 0


def _party_members_list(party) -> list:
    """Привести members к List[int]. В БД может быть list смешанного формата."""
    m = party.members if party.members is not None else []
    if not isinstance(m, list):
        return []
    out = []
    for x in m:
        if isinstance(x, int):
            out.append(x)
        elif isinstance(x, dict) and "id" in x:
            out.append(int(x["id"]))
        elif isinstance(x, (list, tuple)) and len(x) > 0:
            out.append(int(x[0]))
    return out


def _party_to_response(party) -> PartyResponse:
    """Собрать PartyResponse: leader_id — int, members — List[int]."""
    return PartyResponse(
        id=party.id,
        name=party.name,
        leader_id=_party_leader_id(party),
        members=_party_members_list(party),
        created_at=party.created_at,
        updated_at=party.updated_at,
    )


@router.post("/parties", response_model=PartyResponse, status_code=201)
async def create_party_endpoint(
    party_data: PartyCreate, player: Player = Depends(get_current_player)
):
    """Create a new party (leader is added to members, analytics updated)"""
    party = await create_party(leader=player, name=party_data.name)
    party = await add_party_member(party=party, player=player)
    analytics = await get_player_analytics(player)
    if not analytics:
        analytics = await create_player_analytics(player)
    await update_player_analytics(analytics, party_id=party)
    await party.fetch_related("leader_id")
    return _party_to_response(party)


@router.get("/parties", response_model=List[PartyResponse])
async def get_parties_endpoint(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get parties"""
    pagination = validate_pagination(page=page, per_page=per_page)
    parties = await get_parties(
        limit=pagination["per_page"],
        offset=(pagination["page"] - 1) * pagination["per_page"],
    )
    for p in parties:
        await p.fetch_related("leader_id")
    return [_party_to_response(p) for p in parties]


@router.get("/parties/{party_id}", response_model=PartyResponse)
async def get_party_endpoint(
    party_id: int, player: Player = Depends(get_current_player)
):
    """Get party by ID"""
    party = await get_party(party_id)
    if not party:
        raise NotFoundError("Party not found")
    await party.fetch_related("leader_id")
    return _party_to_response(party)


@router.put("/parties/{party_id}", response_model=PartyResponse)
async def update_party_endpoint(
    party_id: int,
    party_data: PartyUpdate,
    player: Player = Depends(get_current_player),
):
    """Update party (only leader)"""
    party = await get_party(party_id)
    if not party:
        raise NotFoundError("Party not found")

    await party.fetch_related("leader_id")
    if _party_leader_id(party) != player.id:
        raise ForbiddenError("Only leader can update party")

    updated = await update_party(party=party, name=party_data.name)
    await updated.fetch_related("leader_id")
    return _party_to_response(updated)


@router.delete("/parties/{party_id}", response_model=SuccessResponse)
async def delete_party_endpoint(
    party_id: int, player: Player = Depends(get_current_player)
):
    """Delete party (only leader)"""
    party = await get_party(party_id)
    if not party:
        raise NotFoundError("Party not found")

    await party.fetch_related("leader_id")
    if _party_leader_id(party) != player.id:
        raise ForbiddenError("Only leader can delete party")

    await delete_party(party)
    return SuccessResponse(message="Party deleted successfully")


@router.post("/parties/{party_id}/members", response_model=PartyResponse)
async def add_party_member_endpoint(
    party_id: int,
    member_data: PartyMemberAdd,
    player: Player = Depends(get_current_player),
):
    """Add member to party"""
    party = await get_party(party_id)
    if not party:
        raise NotFoundError("Party not found")

    new_member = await get_player_by_id(member_data.player_id)
    if not new_member:
        raise NotFoundError("Player not found")

    analytics = await get_player_analytics(new_member)
    if not analytics:
        analytics = await create_player_analytics(new_member)
    await update_player_analytics(analytics, party_id=party)
    updated = await add_party_member(party=party, player=new_member)

    await updated.fetch_related("leader_id")
    return _party_to_response(updated)


@router.delete("/parties/{party_id}/members/{member_id}", response_model=PartyResponse)
async def remove_party_member_endpoint(
    party_id: int, member_id: int, player: Player = Depends(get_current_player)
):
    """Remove member from party"""
    party = await get_party(party_id)
    if not party:
        raise NotFoundError("Party not found")

    member = await get_player_by_id(member_id)
    if not member:
        raise NotFoundError("Member not found")

    await party.fetch_related("leader_id")
    if _party_leader_id(party) != player.id and member_id != player.id:
        raise ForbiddenError("Insufficient permissions")

    updated = await remove_party_member(party=party, player=member)
    await updated.fetch_related("leader_id")
    return _party_to_response(updated)


@router.post("/parties/{party_id}/transfer-leadership", response_model=PartyResponse)
async def transfer_party_leadership_endpoint(
    party_id: int,
    new_leader_id: int,
    player: Player = Depends(get_current_player),
):
    """Transfer party leadership (only current leader)"""
    party = await get_party(party_id)
    if not party:
        raise NotFoundError("Party not found")

    await party.fetch_related("leader_id")
    if _party_leader_id(party) != player.id:
        raise ForbiddenError("Only leader can transfer leadership")

    new_leader = await get_player_by_id(new_leader_id)
    if not new_leader:
        raise NotFoundError("New leader not found")

    updated = await change_party_leader(party=party, new_leader=new_leader)
    await updated.fetch_related("leader_id")
    return _party_to_response(updated)
