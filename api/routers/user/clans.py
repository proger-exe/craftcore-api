"""
User clans router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from api.schemas.clans import (
    ClanCreate,
    ClanResponse,
    ClanUpdate,
    ClanMemberAdd,
    ClanMemberUpdate,
)
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player, validate_pagination
from core.models.players.players import Player
from core.models.social.clans import ClanRole
from core.managers.social.clans import (
    create_clan,
    get_clan,
    get_clans,
    search_clans,
    update_clan,
    delete_clan,
    add_clan_member,
    remove_clan_member,
    update_clan_member_role,
)
from core.managers.players.players import get_player as get_player_by_id
from core.managers.players.profile import (
    get_player_analytics,
    create_player_analytics,
    update_player_analytics,
)
from core.shared.errors import ForbiddenError, NotFoundError

router = APIRouter(prefix="/user", tags=["user", "clans"])


def _clan_owner_id(clan) -> int:
    """owner_id в Tortoise может быть int или Player — в ответ всегда int."""
    o = getattr(clan, "owner_id", None)
    if isinstance(o, int):
        return int(o)
    if hasattr(o, "id") and type(o).__name__ != "QuerySet":
        return int(o.id)
    raw = getattr(clan, "__dict__", {}).get("owner_id")
    return int(raw) if raw is not None else 0


def _members_to_dict(members) -> dict:
    """Привести members к dict: ключ str(player_id), значение [id, role]. Для проверки прав."""
    if isinstance(members, dict):
        return members
    if not isinstance(members, list):
        return {}
    out = {}
    for m in members:
        if isinstance(m, dict):
            pid, role = m.get("id"), m.get("role")
            if pid is not None:
                out[str(pid)] = [pid, role]
        elif isinstance(m, list) and len(m) >= 2:
            out[str(m[0])] = [m[0], m[1]]
    return out


def _members_to_response_list(members) -> list:
    """Формат для ответа: список [id, role], каждый элемент — массив (ожидание плагина)."""
    d = _members_to_dict(members)
    out = []
    for pid in sorted(d.keys(), key=int):
        id_role = d[pid]
        pid_int = id_role[0]
        role = id_role[1]
        role_str = getattr(role, "value", role)
        out.append([pid_int, role_str])
    return out


def _player_in_clan(clan, player_id: int) -> bool:
    """Проверка: игрок в клане (владелец или любой участник)."""
    if _clan_owner_id(clan) == player_id:
        return True
    members = _members_to_dict(clan.members or [])
    return str(player_id) in members


def _player_can_manage_clan(clan, player_id: int) -> bool:
    """Проверка: игрок — владелец или лидер/модератор в клане. Роль в БД может быть строкой."""
    if _clan_owner_id(clan) == player_id:
        return True
    members = _members_to_dict(clan.members or [])
    player_member = members.get(str(player_id))
    if not player_member:
        return False
    role = player_member[1]
    role_str = getattr(role, "value", role)
    return role_str in ("leader", "moderator")


def _clan_to_response(clan) -> ClanResponse:
    """Собрать ClanResponse: members — List[[id, role]] под ожидание плагина (BEGIN_ARRAY)."""
    owner_id = _clan_owner_id(clan)
    members = _members_to_response_list(clan.members or [])
    homes = clan.homes if isinstance(clan.homes, list) else []
    return ClanResponse(
        id=clan.id,
        owner_id=owner_id,
        members=members,
        name=clan.name,
        description=clan.description,
        tag=clan.tag,
        prefix=clan.prefix,
        inventory=[],
        balance=clan.balance,
        homes=homes,
        created_at=clan.created_at,
        updated_at=clan.updated_at,
    )


@router.post("/clans", response_model=ClanResponse, status_code=201)
async def create_clan_endpoint(
    clan_data: ClanCreate, player: Player = Depends(get_current_player)
):
    """Create a new clan (creator is added as leader with max rights)"""
    clan = await create_clan(
        owner=player,
        name=clan_data.name,
        tag=clan_data.tag,
        description=clan_data.description,
        prefix=clan_data.prefix,
    )
    clan = await add_clan_member(clan, player, ClanRole.LEADER)
    analytics = await get_player_analytics(player)
    if not analytics:
        analytics = await create_player_analytics(player)
    await update_player_analytics(analytics, clan_id=clan)
    return _clan_to_response(clan)


@router.get("/clans", response_model=List[ClanResponse])
async def get_clans_endpoint(
    name: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get clans with optional filters"""
    pagination = validate_pagination(page=page, per_page=per_page)

    if search:
        clans = await search_clans(query=search)
    else:
        clans = await get_clans(
            name=name,
            tag=tag,
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )

    return [_clan_to_response(c) for c in clans]


@router.get("/clans/{clan_id}", response_model=ClanResponse)
async def get_clan_endpoint(clan_id: int, player: Player = Depends(get_current_player)):
    """Get clan by ID"""
    clan = await get_clan(clan_id)
    if not clan:
        raise NotFoundError("Clan not found")
    return _clan_to_response(clan)


@router.put("/clans/{clan_id}", response_model=ClanResponse)
async def update_clan_endpoint(
    clan_id: int,
    clan_data: ClanUpdate,
    player: Player = Depends(get_current_player),
):
    """Update clan (любой участник клана может обновлять, в т.ч. дома; инвентарь через API отключён)"""
    clan = await get_clan(clan_id)
    if not clan:
        raise NotFoundError("Clan not found")
    await clan.fetch_related("owner_id")

    if not _player_in_clan(clan, player.id):
        raise ForbiddenError("Not a clan member")

    updated = await update_clan(
        clan=clan,
        name=clan_data.name,
        description=clan_data.description,
        tag=clan_data.tag,
        prefix=clan_data.prefix,
        homes=clan_data.homes,
    )
    return _clan_to_response(updated)


@router.delete("/clans/{clan_id}", response_model=SuccessResponse)
async def delete_clan_endpoint(
    clan_id: int, player: Player = Depends(get_current_player)
):
    """Delete clan (only owner)"""
    clan = await get_clan(clan_id)
    if not clan:
        raise NotFoundError("Clan not found")
    await clan.fetch_related("owner_id")

    if _clan_owner_id(clan) != player.id:
        raise ForbiddenError("Only owner can delete clan")

    await delete_clan(clan)
    return SuccessResponse(message="Clan deleted successfully")


@router.post("/clans/{clan_id}/members", response_model=ClanResponse)
async def add_clan_member_endpoint(
    clan_id: int,
    member_data: ClanMemberAdd,
    player: Player = Depends(get_current_player),
):
    """Add member to clan (only owner or moderator)"""
    clan = await get_clan(clan_id)
    if not clan:
        raise NotFoundError("Clan not found")
    await clan.fetch_related("owner_id")

    if not _player_can_manage_clan(clan, player.id):
        raise ForbiddenError("Insufficient permissions")

    new_member = await get_player_by_id(member_data.player_id)
    if not new_member:
        raise NotFoundError("Player not found")

    analytics = await get_player_analytics(new_member)
    if not analytics:
        analytics = await create_player_analytics(new_member)
    await update_player_analytics(analytics, clan_id=clan)

    updated = await add_clan_member(
        clan=clan, player=new_member, role=member_data.role
    )

    return _clan_to_response(updated)


@router.delete("/clans/{clan_id}/members/{member_id}", response_model=ClanResponse)
async def remove_clan_member_endpoint(
    clan_id: int, member_id: int, player: Player = Depends(get_current_player)
):
    """Remove member from clan"""
    clan = await get_clan(clan_id)
    if not clan:
        raise NotFoundError("Clan not found")

    member = await get_player_by_id(member_id)
    if not member:
        raise NotFoundError("Member not found")
    await clan.fetch_related("owner_id")

    if member_id != player.id and not _player_can_manage_clan(clan, player.id):
        raise ForbiddenError("Insufficient permissions")

    updated = await remove_clan_member(clan=clan, player=member)
    analytics = await get_player_analytics(member)
    if analytics:
        await update_player_analytics(analytics, clan_id=None)
    return _clan_to_response(updated)


@router.put("/clans/{clan_id}/members/{member_id}/role", response_model=ClanResponse)
async def update_clan_member_role_endpoint(
    clan_id: int,
    member_id: int,
    role_data: ClanMemberUpdate,
    player: Player = Depends(get_current_player),
):
    """Update clan member role (only owner)"""
    clan = await get_clan(clan_id)
    if not clan:
        raise NotFoundError("Clan not found")
    await clan.fetch_related("owner_id")

    if _clan_owner_id(clan) != player.id:
        raise ForbiddenError("Only owner can change roles")

    member = await get_player_by_id(member_id)
    if not member:
        raise NotFoundError("Member not found")

    updated = await update_clan_member_role(
        clan=clan, player=member, role=role_data.role
    )
    return _clan_to_response(updated)
