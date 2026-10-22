"""
Safety manager for CRUD operations on Ban, Mute, Warn, Arrest, and AdminActionLog models
"""

from typing import Optional, List, Union
from datetime import datetime
from tortoise.expressions import Q
from core.models.safety.moderation import Ban, Mute, Warn, Arrest, AdminActionLog
from core.models.players.players import Player
from core.shared.db import locked_row
from core.shared.logger import logger
from core.shared.utils import to_id


async def _get_active_moderation_row(model_cls, player: Player, allow_permanent: bool):
    """
    Shared active-status query for Ban/Mute/Arrest.

    allow_permanent=True also matches rows with expires_at=None (bans can be
    permanent); allow_permanent=False requires expires_at in the future
    (mutes/arrests always have expires_at set, per their model definitions).
    """
    now = datetime.now()
    query = model_cls.filter(player=player, is_active=True)
    if allow_permanent:
        query = query.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
    else:
        query = query.filter(expires_at__gt=now)
    return await query.first()


# Ban CRUD operations


async def ban_player(
    player: Player,
    reason: str,
    admin: Optional[Player] = None,
    expires_at: Optional[datetime] = None,
) -> Ban:
    """
    Create a ban for player

    Args:
        player: Player to ban
        reason: Ban reason
        admin: Admin who bans (optional, None for system ban)
        expires_at: Expiration time (optional, None for permanent ban)

    Returns:
        Ban: Created ban instance

    Raises:
        Exception: If creation fails
    """
    try:
        ban = await Ban.create(
            player=player,
            admin=admin,
            reason=reason,
            expires_at=expires_at,
            is_active=True,
        )
        logger.info(
            "🚫 Player banned",
            ban_id=ban.id,
            player_id=player.id,
            admin_id=admin.id if admin else None,
            expires_at=expires_at,
        )
        return ban
    except Exception as e:
        logger.error("Failed to ban player", error=str(e), player_id=player.id)
        raise


async def get_ban(ban: Union[int, Ban]) -> Optional[Ban]:
    """
    Get ban by ID или по экземпляру Ban.

    Args:
        ban: id бана (int) или экземпляр Ban

    Returns:
        Ban or None if not found
    """
    try:
        bid = to_id(ban)
        return await Ban.get_or_none(id=bid)
    except Exception as e:
        logger.error("Failed to get ban", error=str(e), ban_id=to_id(ban))
        raise


async def get_player_bans(player: Player, active_only: bool = False) -> List[Ban]:
    """
    Get all bans for player

    Args:
        player: Player instance
        active_only: Return only active bans

    Returns:
        List of Ban instances
    """
    try:
        query = Ban.filter(player=player)
        if active_only:
            query = query.filter(is_active=True)
        return await query.all()
    except Exception as e:
        logger.error("Failed to get player bans", error=str(e), player_id=player.id)
        raise


async def is_player_banned(player: Player) -> bool:
    """
    Check if player has active ban

    Args:
        player: Player instance

    Returns:
        True if player is banned, False otherwise
    """
    try:
        active_ban = await _get_active_moderation_row(Ban, player, allow_permanent=True)
        return active_ban is not None
    except Exception as e:
        logger.error(
            "Failed to check if player banned", error=str(e), player_id=player.id
        )
        raise


async def get_active_ban(player: Player) -> Optional[Ban]:
    """
    Get active ban for player

    Args:
        player: Player instance

    Returns:
        Active Ban or None if not banned
    """
    try:
        return await _get_active_moderation_row(Ban, player, allow_permanent=True)
    except Exception as e:
        logger.error("Failed to get active ban", error=str(e), player_id=player.id)
        raise


async def unban_player(ban: Ban, unbanned_by: Optional[Player] = None) -> Ban:
    """
    Unban player

    Args:
        ban: Ban instance to deactivate
        unbanned_by: Admin who unbans (optional)

    Returns:
        Updated Ban instance

    Raises:
        Exception: If update fails
    """
    try:
        async with locked_row(Ban, id=ban.id) as locked_ban:
            locked_ban.is_active = False
            locked_ban.unbanned_at = datetime.now()
            locked_ban.unbanned_by = unbanned_by
            await locked_ban.save()

        await locked_ban.fetch_related("player")
        logger.info(
            "✅ Player unbanned",
            ban_id=locked_ban.id,
            player_id=locked_ban.player.id,
            unbanned_by_id=unbanned_by.id if unbanned_by else None,
        )
        return locked_ban
    except Exception as e:
        logger.error("Failed to unban player", error=str(e), ban_id=ban.id)
        raise


async def delete_ban(ban: Ban) -> None:
    """
    Delete ban

    Args:
        ban: Ban instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        ban_id = ban.id
        await ban.delete()
        logger.info("🗑️ Ban deleted", ban_id=ban_id)
    except Exception as e:
        logger.error("Failed to delete ban", error=str(e), ban_id=ban_id)
        raise


# Mute CRUD operations


async def mute_player(
    player: Player,
    reason: str,
    expires_at: datetime,
    admin: Optional[Player] = None,
) -> Mute:
    """
    Create a mute for player

    Args:
        player: Player to mute
        reason: Mute reason
        expires_at: Expiration time (required)
        admin: Admin who mutes (optional, None for system mute)

    Returns:
        Mute: Created mute instance

    Raises:
        Exception: If creation fails
    """
    try:
        mute = await Mute.create(
            player=player,
            admin=admin,
            reason=reason,
            expires_at=expires_at,
            is_active=True,
        )
        logger.info(
            "🔇 Player muted",
            mute_id=mute.id,
            player_id=player.id,
            admin_id=admin.id if admin else None,
            expires_at=expires_at,
        )
        return mute
    except Exception as e:
        logger.error("Failed to mute player", error=str(e), player_id=player.id)
        raise


async def get_mute(mute: Union[int, Mute]) -> Optional[Mute]:
    """
    Get mute by ID или по экземпляру Mute.

    Args:
        mute: id мута (int) или экземпляр Mute

    Returns:
        Mute or None if not found
    """
    try:
        mid = to_id(mute)
        return await Mute.get_or_none(id=mid)
    except Exception as e:
        logger.error("Failed to get mute", error=str(e), mute_id=to_id(mute))
        raise


async def get_player_mutes(player: Player, active_only: bool = False) -> List[Mute]:
    """
    Get all mutes for player

    Args:
        player: Player instance
        active_only: Return only active mutes

    Returns:
        List of Mute instances
    """
    try:
        query = Mute.filter(player=player)
        if active_only:
            query = query.filter(is_active=True)
        return await query.all()
    except Exception as e:
        logger.error("Failed to get player mutes", error=str(e), player_id=player.id)
        raise


async def is_player_muted(player: Player) -> bool:
    """
    Check if player has active mute

    Args:
        player: Player instance

    Returns:
        True if player is muted, False otherwise
    """
    try:
        active_mute = await _get_active_moderation_row(
            Mute, player, allow_permanent=False
        )
        return active_mute is not None
    except Exception as e:
        logger.error(
            "Failed to check if player muted", error=str(e), player_id=player.id
        )
        raise


async def get_active_mute(player: Player) -> Optional[Mute]:
    """
    Get active mute for player

    Args:
        player: Player instance

    Returns:
        Active Mute or None if not muted
    """
    try:
        return await _get_active_moderation_row(Mute, player, allow_permanent=False)
    except Exception as e:
        logger.error("Failed to get active mute", error=str(e), player_id=player.id)
        raise


async def unmute_player(mute: Mute) -> Mute:
    """
    Unmute player

    Args:
        mute: Mute instance to deactivate

    Returns:
        Updated Mute instance

    Raises:
        Exception: If update fails
    """
    try:
        async with locked_row(Mute, id=mute.id) as locked_mute:
            locked_mute.is_active = False
            await locked_mute.save(update_fields=["is_active"])

        await locked_mute.fetch_related("player")
        logger.info(
            "🔊 Player unmuted", mute_id=locked_mute.id, player_id=locked_mute.player.id
        )
        return locked_mute
    except Exception as e:
        logger.error("Failed to unmute player", error=str(e), mute_id=mute.id)
        raise


async def delete_mute(mute: Mute) -> None:
    """
    Delete mute

    Args:
        mute: Mute instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        mute_id = mute.id
        await mute.delete()
        logger.info("🗑️ Mute deleted", mute_id=mute_id)
    except Exception as e:
        logger.error("Failed to delete mute", error=str(e), mute_id=mute_id)
        raise


# Warn CRUD operations


async def warn_player(
    player: Player,
    reason: str,
    admin: Player,
) -> Warn:
    """
    Create a warn for player

    Args:
        player: Player to warn
        reason: Warn reason
        admin: Admin who warns

    Returns:
        Warn: Created warn instance

    Raises:
        Exception: If creation fails
    """
    try:
        warn = await Warn.create(
            player=player,
            admin=admin,
            reason=reason,
            is_active=True,
        )
        logger.info(
            "⚠️ Player warned",
            warn_id=warn.id,
            player_id=player.id,
            admin_id=admin.id,
        )
        return warn
    except Exception as e:
        logger.error("Failed to warn player", error=str(e), player_id=player.id)
        raise


async def get_warn(warn: Union[int, Warn]) -> Optional[Warn]:
    """
    Get warn by ID или по экземпляру Warn.

    Args:
        warn: id варна (int) или экземпляр Warn

    Returns:
        Warn or None if not found
    """
    try:
        wid = to_id(warn)
        return await Warn.get_or_none(id=wid)
    except Exception as e:
        logger.error("Failed to get warn", error=str(e), warn_id=to_id(warn))
        raise


async def get_player_warns(player: Player, active_only: bool = False) -> List[Warn]:
    """
    Get all warns for player

    Args:
        player: Player instance
        active_only: Return only active warns

    Returns:
        List of Warn instances
    """
    try:
        query = Warn.filter(player=player)
        if active_only:
            query = query.filter(is_active=True)
        return await query.all()
    except Exception as e:
        logger.error("Failed to get player warns", error=str(e), player_id=player.id)
        raise


async def deactivate_warn(warn: Warn) -> Warn:
    """
    Deactivate warn

    Args:
        warn: Warn instance to deactivate

    Returns:
        Updated Warn instance

    Raises:
        Exception: If update fails
    """
    try:
        async with locked_row(Warn, id=warn.id) as locked_warn:
            locked_warn.is_active = False
            await locked_warn.save(update_fields=["is_active"])

        logger.info("✅ Warn deactivated", warn_id=locked_warn.id)
        return locked_warn
    except Exception as e:
        logger.error("Failed to deactivate warn", error=str(e), warn_id=warn.id)
        raise


async def delete_warn(warn: Warn) -> None:
    """
    Delete warn

    Args:
        warn: Warn instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        warn_id = warn.id
        await warn.delete()
        logger.info("🗑️ Warn deleted", warn_id=warn_id)
    except Exception as e:
        logger.error("Failed to delete warn", error=str(e), warn_id=warn_id)
        raise


# Arrest CRUD operations


async def arrest_player(
    player: Player,
    reason: str,
    expires_at: datetime,
    admin: Optional[Player] = None,
) -> Arrest:
    """
    Create an arrest for player

    Args:
        player: Player to arrest
        reason: Arrest reason
        expires_at: Expiration time (required)
        admin: Admin who arrests (optional, None for system arrest)

    Returns:
        Arrest: Created arrest instance

    Raises:
        Exception: If creation fails
    """
    try:
        arrest = await Arrest.create(
            player=player,
            admin=admin,
            reason=reason,
            expires_at=expires_at,
            is_active=True,
        )
        logger.info(
            "🔒 Player arrested",
            arrest_id=arrest.id,
            player_id=player.id,
            admin_id=admin.id if admin else None,
            expires_at=expires_at,
        )
        return arrest
    except Exception as e:
        logger.error("Failed to arrest player", error=str(e), player_id=player.id)
        raise


async def get_arrest(arrest: Union[int, Arrest]) -> Optional[Arrest]:
    """
    Get arrest by ID или по экземпляру Arrest.

    Args:
        arrest: id ареста (int) или экземпляр Arrest

    Returns:
        Arrest or None if not found
    """
    try:
        aid = to_id(arrest)
        return await Arrest.get_or_none(id=aid)
    except Exception as e:
        logger.error("Failed to get arrest", error=str(e), arrest_id=to_id(arrest))
        raise


async def get_player_arrests(player: Player, active_only: bool = False) -> List[Arrest]:
    """
    Get all arrests for player

    Args:
        player: Player instance
        active_only: Return only active arrests

    Returns:
        List of Arrest instances
    """
    try:
        query = Arrest.filter(player=player)
        if active_only:
            query = query.filter(is_active=True)
        return await query.all()
    except Exception as e:
        logger.error("Failed to get player arrests", error=str(e), player_id=player.id)
        raise


async def is_player_arrested(player: Player) -> bool:
    """
    Check if player has active arrest

    Args:
        player: Player instance

    Returns:
        True if player is arrested, False otherwise
    """
    try:
        active_arrest = await _get_active_moderation_row(
            Arrest, player, allow_permanent=False
        )
        return active_arrest is not None
    except Exception as e:
        logger.error(
            "Failed to check if player arrested", error=str(e), player_id=player.id
        )
        raise


async def get_active_arrest(player: Player) -> Optional[Arrest]:
    """
    Get active arrest for player

    Args:
        player: Player instance

    Returns:
        Active Arrest or None if not arrested
    """
    try:
        return await _get_active_moderation_row(Arrest, player, allow_permanent=False)
    except Exception as e:
        logger.error("Failed to get active arrest", error=str(e), player_id=player.id)
        raise


async def release_player(arrest: Arrest, released_by: Optional[Player] = None) -> Arrest:
    """
    Release player from arrest (early release)

    Args:
        arrest: Arrest instance to deactivate
        released_by: Admin who releases (optional)

    Returns:
        Updated Arrest instance

    Raises:
        Exception: If update fails
    """
    try:
        async with locked_row(Arrest, id=arrest.id) as locked_arrest:
            locked_arrest.is_active = False
            locked_arrest.released_at = datetime.now()
            locked_arrest.released_by = released_by
            await locked_arrest.save()

        await locked_arrest.fetch_related("player")
        logger.info(
            "✅ Player released from arrest",
            arrest_id=locked_arrest.id,
            player_id=locked_arrest.player.id,
            released_by_id=released_by.id if released_by else None,
        )
        return locked_arrest
    except Exception as e:
        logger.error("Failed to release player", error=str(e), arrest_id=arrest.id)
        raise


async def delete_arrest(arrest: Arrest) -> None:
    """
    Delete arrest

    Args:
        arrest: Arrest instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        arrest_id = arrest.id
        await arrest.delete()
        logger.info("🗑️ Arrest deleted", arrest_id=arrest_id)
    except Exception as e:
        logger.error("Failed to delete arrest", error=str(e), arrest_id=arrest_id)
        raise


# AdminActionLog CRUD operations


async def log_admin_action(
    admin: Player,
    action_type: str,
    target_player: Optional[Player] = None,
    details: Optional[dict] = None,
) -> AdminActionLog:
    """
    Log admin action

    Args:
        admin: Admin who performed action
        action_type: Type of action (ban, mute, warn, kick, etc.)
        target_player: Target player (optional)
        details: Action details (optional)

    Returns:
        AdminActionLog: Created log entry

    Raises:
        Exception: If creation fails
    """
    try:
        log = await AdminActionLog.create(
            admin=admin,
            action_type=action_type,
            target_player=target_player,
            details=details or {},
        )
        logger.info(
            "📝 Admin action logged",
            log_id=log.id,
            admin_id=admin.id,
            action_type=action_type,
            target_player_id=target_player.id if target_player else None,
        )
        return log
    except Exception as e:
        logger.error("Failed to log admin action", error=str(e), admin_id=admin.id)
        raise


async def get_admin_log(log: Union[int, AdminActionLog]) -> Optional[AdminActionLog]:
    """
    Get admin log by ID или по экземпляру AdminActionLog.

    Args:
        log: id записи лога (int) или экземпляр AdminActionLog

    Returns:
        AdminActionLog or None if not found
    """
    try:
        lid = to_id(log)
        return await AdminActionLog.get_or_none(id=lid)
    except Exception as e:
        logger.error("Failed to get admin log", error=str(e), log_id=to_id(log))
        raise


async def get_admin_logs(
    admin: Optional[Player] = None,
    action_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[AdminActionLog]:
    """
    Get admin logs with optional filters

    Args:
        admin: Filter by admin (optional)
        action_type: Filter by action type (optional)
        limit: Maximum number of logs to return
        offset: Number of logs to skip

    Returns:
        List of AdminActionLog instances
    """
    try:
        query = AdminActionLog.all()

        if admin is not None:
            query = query.filter(admin=admin)
        if action_type is not None:
            query = query.filter(action_type=action_type)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error("Failed to get admin logs", error=str(e))
        raise


async def get_target_player_logs(
    target_player: Player,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[AdminActionLog]:
    """
    Get admin logs for target player

    Args:
        target_player: Target player
        limit: Maximum number of logs to return
        offset: Number of logs to skip

    Returns:
        List of AdminActionLog instances
    """
    try:
        query = AdminActionLog.filter(target_player=target_player)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error(
            "Failed to get target player logs", error=str(e), player_id=target_player.id
        )
        raise
