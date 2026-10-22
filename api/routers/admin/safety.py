"""
Admin safety router for moderation endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from api.schemas.safety import (
    BanCreate,
    BanResponse,
    MuteCreate,
    MuteResponse,
    WarnCreate,
    WarnResponse,
    ArrestCreate,
    ArrestResponse,
    AdminActionLogResponse,
)
from api.schemas.common import PaginatedResponse, SuccessResponse
from api.dependencies import get_current_admin, validate_pagination
from core.models.players.players import Player
from core.managers.safety.moderation import (
    ban_player,
    get_ban,
    get_player_bans,
    get_active_ban,
    unban_player,
    delete_ban,
    is_player_banned,
    mute_player,
    get_mute,
    get_player_mutes,
    get_active_mute,
    unmute_player,
    delete_mute,
    is_player_muted,
    warn_player,
    get_warn,
    get_player_warns,
    delete_warn,
    arrest_player,
    get_arrest,
    get_player_arrests,
    get_active_arrest,
    release_player,
    delete_arrest,
    is_player_arrested,
    log_admin_action,
    get_admin_logs,
    get_target_player_logs,
)
from core.managers.players.players import get_player as get_player_by_id
from core.shared.logger import logger

router = APIRouter(prefix="/admin", tags=["admin", "safety"])


# Ban endpoints


@router.post("/bans", response_model=BanResponse, status_code=201)
async def create_ban(ban_data: BanCreate, admin: Player = Depends(get_current_admin)):
    """Create a ban for a player"""
    try:
        player = await get_player_by_id(ban_data.player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        ban = await ban_player(
            player=player,
            reason=ban_data.reason,
            admin=admin,
            expires_at=ban_data.expires_at,
        )

        await log_admin_action(
            admin=admin,
            action_type="ban",
            target_player=player,
            details={"reason": ban_data.reason, "expires_at": str(ban_data.expires_at)},
        )

        return BanResponse.model_validate(ban)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create ban via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bans/{ban_id}", response_model=BanResponse)
async def get_ban_by_id(ban_id: int, admin: Player = Depends(get_current_admin)):
    """Get ban by ID"""
    ban = await get_ban(ban_id)
    if not ban:
        raise HTTPException(status_code=404, detail="Ban not found")
    return BanResponse.model_validate(ban)


@router.get("/bans/player/{player_id}", response_model=List[BanResponse])
async def get_bans_by_player(
    player_id: int = Path(..., description="Player ID"),
    active_only: bool = Query(False),
    admin: Player = Depends(get_current_admin),
):
    """Get all bans for a player"""
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    bans = await get_player_bans(player, active_only=active_only)
    return [BanResponse.model_validate(ban) for ban in bans]


@router.get("/bans/player/{player_id}/check", response_model=dict)
async def check_player_banned(
    player_id: int = Path(..., description="Player ID"),
    admin: Player = Depends(get_current_admin),
):
    """Check if player is currently banned"""
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    is_banned = await is_player_banned(player)
    active_ban = await get_active_ban(player) if is_banned else None

    return {
        "is_banned": is_banned,
        "ban": BanResponse.model_validate(active_ban) if active_ban else None,
    }


@router.post("/bans/{ban_id}/unban", response_model=BanResponse)
async def unban_player_endpoint(
    ban_id: int, admin: Player = Depends(get_current_admin)
):
    """Unban a player"""
    ban = await get_ban(ban_id)
    if not ban:
        raise HTTPException(status_code=404, detail="Ban not found")

    updated_ban = await unban_player(ban, unbanned_by=admin)

    await log_admin_action(
        admin=admin,
        action_type="unban",
        target_player=ban.player,
        details={"ban_id": ban_id},
    )

    return BanResponse.model_validate(updated_ban)


@router.delete("/bans/{ban_id}", response_model=SuccessResponse)
async def delete_ban_endpoint(ban_id: int, admin: Player = Depends(get_current_admin)):
    """Delete a ban"""
    ban = await get_ban(ban_id)
    if not ban:
        raise HTTPException(status_code=404, detail="Ban not found")

    await delete_ban(ban)
    return SuccessResponse(message="Ban deleted successfully")


# Mute endpoints


@router.post("/mutes", response_model=MuteResponse, status_code=201)
async def create_mute(
    mute_data: MuteCreate, admin: Player = Depends(get_current_admin)
):
    """Create a mute for a player"""
    try:
        player = await get_player_by_id(mute_data.player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        mute = await mute_player(
            player=player,
            reason=mute_data.reason,
            expires_at=mute_data.expires_at,
            admin=admin,
        )

        await log_admin_action(
            admin=admin,
            action_type="mute",
            target_player=player,
            details={
                "reason": mute_data.reason,
                "expires_at": str(mute_data.expires_at),
            },
        )

        return MuteResponse.model_validate(mute)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create mute via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mutes/{mute_id}", response_model=MuteResponse)
async def get_mute_by_id(mute_id: int, admin: Player = Depends(get_current_admin)):
    """Get mute by ID"""
    mute = await get_mute(mute_id)
    if not mute:
        raise HTTPException(status_code=404, detail="Mute not found")
    return MuteResponse.model_validate(mute)


@router.get("/mutes/player/{player_id}", response_model=List[MuteResponse])
async def get_mutes_by_player(
    player_id: int = Path(..., description="Player ID"),
    active_only: bool = Query(False),
    admin: Player = Depends(get_current_admin),
):
    """Get all mutes for a player"""
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    mutes = await get_player_mutes(player, active_only=active_only)
    return [MuteResponse.model_validate(mute) for mute in mutes]


@router.get("/mutes/player/{player_id}/check", response_model=dict)
async def check_player_muted(
    player_id: int = Path(..., description="Player ID"),
    admin: Player = Depends(get_current_admin),
):
    """Check if player is currently muted"""
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    is_muted = await is_player_muted(player)
    active_mute = await get_active_mute(player) if is_muted else None

    return {
        "is_muted": is_muted,
        "mute": MuteResponse.model_validate(active_mute) if active_mute else None,
    }


@router.post("/mutes/{mute_id}/unmute", response_model=MuteResponse)
async def unmute_player_endpoint(
    mute_id: int, admin: Player = Depends(get_current_admin)
):
    """Unmute a player"""
    mute = await get_mute(mute_id)
    if not mute:
        raise HTTPException(status_code=404, detail="Mute not found")

    updated_mute = await unmute_player(mute)

    await log_admin_action(
        admin=admin,
        action_type="unmute",
        target_player=mute.player,
        details={"mute_id": mute_id},
    )

    return MuteResponse.model_validate(updated_mute)


@router.delete("/mutes/{mute_id}", response_model=SuccessResponse)
async def delete_mute_endpoint(
    mute_id: int, admin: Player = Depends(get_current_admin)
):
    """Delete a mute"""
    mute = await get_mute(mute_id)
    if not mute:
        raise HTTPException(status_code=404, detail="Mute not found")

    await delete_mute(mute)
    return SuccessResponse(message="Mute deleted successfully")


# Warn endpoints


@router.post("/warns", response_model=WarnResponse, status_code=201)
async def create_warn(
    warn_data: WarnCreate, admin: Player = Depends(get_current_admin)
):
    """Create a warn for a player"""
    try:
        player = await get_player_by_id(warn_data.player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        warn = await warn_player(
            player=player,
            reason=warn_data.reason,
            admin=admin,
        )

        await log_admin_action(
            admin=admin,
            action_type="warn",
            target_player=player,
            details={"reason": warn_data.reason},
        )

        return WarnResponse.model_validate(warn)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create warn via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warns/{warn_id}", response_model=WarnResponse)
async def get_warn_by_id(warn_id: int, admin: Player = Depends(get_current_admin)):
    """Get warn by ID"""
    warn = await get_warn(warn_id)
    if not warn:
        raise HTTPException(status_code=404, detail="Warn not found")
    return WarnResponse.model_validate(warn)


@router.get("/warns/player/{player_id}", response_model=List[WarnResponse])
async def get_warns_by_player(
    player_id: int = Path(..., description="Player ID"),
    active_only: bool = Query(False),
    admin: Player = Depends(get_current_admin),
):
    """Get all warns for a player"""
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    warns = await get_player_warns(player, active_only=active_only)
    return [WarnResponse.model_validate(warn) for warn in warns]


@router.delete("/warns/{warn_id}", response_model=SuccessResponse)
async def delete_warn_endpoint(
    warn_id: int, admin: Player = Depends(get_current_admin)
):
    """Delete a warn"""
    warn = await get_warn(warn_id)
    if not warn:
        raise HTTPException(status_code=404, detail="Warn not found")

    await delete_warn(warn)
    return SuccessResponse(message="Warn deleted successfully")


# Arrest endpoints


@router.post("/arrests", response_model=ArrestResponse, status_code=201)
async def create_arrest(
    arrest_data: ArrestCreate, admin: Player = Depends(get_current_admin)
):
    """Create an arrest for a player"""
    try:
        player = await get_player_by_id(arrest_data.player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        arrest = await arrest_player(
            player=player,
            reason=arrest_data.reason,
            expires_at=arrest_data.expires_at,
            admin=admin,
        )

        await log_admin_action(
            admin=admin,
            action_type="arrest",
            target_player=player,
            details={
                "reason": arrest_data.reason,
                "expires_at": str(arrest_data.expires_at),
            },
        )

        return ArrestResponse.model_validate(arrest)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create arrest via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/arrests/{arrest_id}", response_model=ArrestResponse)
async def get_arrest_by_id(arrest_id: int, admin: Player = Depends(get_current_admin)):
    """Get arrest by ID"""
    arrest = await get_arrest(arrest_id)
    if not arrest:
        raise HTTPException(status_code=404, detail="Arrest not found")
    return ArrestResponse.model_validate(arrest)


@router.get("/arrests/player/{player_id}", response_model=List[ArrestResponse])
async def get_arrests_by_player(
    player_id: int = Path(..., description="Player ID"),
    active_only: bool = Query(False),
    admin: Player = Depends(get_current_admin),
):
    """Get all arrests for a player"""
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    arrests = await get_player_arrests(player, active_only=active_only)
    return [ArrestResponse.model_validate(arrest) for arrest in arrests]


@router.get("/arrests/player/{player_id}/check", response_model=dict)
async def check_player_arrested(
    player_id: int = Path(..., description="Player ID"),
    admin: Player = Depends(get_current_admin),
):
    """Check if player is currently arrested"""
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    is_arrested = await is_player_arrested(player)
    active_arrest = await get_active_arrest(player) if is_arrested else None

    return {
        "is_arrested": is_arrested,
        "arrest": ArrestResponse.model_validate(active_arrest) if active_arrest else None,
    }


@router.post("/arrests/{arrest_id}/release", response_model=ArrestResponse)
async def release_player_endpoint(
    arrest_id: int, admin: Player = Depends(get_current_admin)
):
    """Release a player from arrest (early release)"""
    arrest = await get_arrest(arrest_id)
    if not arrest:
        raise HTTPException(status_code=404, detail="Arrest not found")

    updated_arrest = await release_player(arrest, released_by=admin)

    await log_admin_action(
        admin=admin,
        action_type="release",
        target_player=arrest.player,
        details={"arrest_id": arrest_id},
    )

    return ArrestResponse.model_validate(updated_arrest)


@router.delete("/arrests/{arrest_id}", response_model=SuccessResponse)
async def delete_arrest_endpoint(
    arrest_id: int, admin: Player = Depends(get_current_admin)
):
    """Delete an arrest"""
    arrest = await get_arrest(arrest_id)
    if not arrest:
        raise HTTPException(status_code=404, detail="Arrest not found")

    await delete_arrest(arrest)
    return SuccessResponse(message="Arrest deleted successfully")


# Admin logs endpoints


@router.get("/logs", response_model=List[AdminActionLogResponse])
async def get_admin_logs_endpoint(
    admin_id: Optional[int] = Query(None),
    action_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_admin: Player = Depends(get_current_admin),
):
    """Get admin action logs"""
    try:
        admin = None
        if admin_id:
            admin = await get_player_by_id(admin_id)
            if not admin:
                raise HTTPException(status_code=404, detail="Admin not found")

        logs = await get_admin_logs(
            admin=admin,
            action_type=action_type,
            limit=limit,
            offset=offset,
        )
        return [AdminActionLogResponse.model_validate(log) for log in logs]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get admin logs via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/player/{player_id}", response_model=List[AdminActionLogResponse])
async def get_player_logs(
    player_id: int = Path(..., description="Player ID"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    admin: Player = Depends(get_current_admin),
):
    """Get admin logs for a specific player"""
    player = await get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    logs = await get_target_player_logs(player, limit=limit, offset=offset)
    return [AdminActionLogResponse.model_validate(log) for log in logs]
