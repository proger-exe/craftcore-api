"""
Players manager for CRUD operations on Player model
"""

import logging
import random
from typing import Optional, List, Union
from tortoise import connections
from tortoise.transactions import in_transaction
from core.models.players.players import Player, PlayerRoles
from core.models.localization.locale import Languages
from core.shared.logger import logger
from core.shared.utils import to_id
from core.managers.economics.utils import validate_amount

_players_log = logging.getLogger("core.managers.players")

# BigInt range for player id (positive, avoid 0)
_PLAYER_ID_MIN = 1
_PLAYER_ID_MAX = 2**63 - 1


def _generate_player_id() -> int:
    """Generate a random positive bigint for player id (DB sequence may be broken)."""
    return random.randint(_PLAYER_ID_MIN, _PLAYER_ID_MAX)


async def create_player(
    tg_id: Optional[int] = None,
    ds_id: Optional[str] = None,
    nickname: Optional[str] = None,
    role: PlayerRoles = PlayerRoles.GUEST,
    balance: int = 0,
    language: Languages = Languages.RU,
    ref_father: Optional[Player] = None,
) -> Player:
    """
    Create a new player with explicitly generated id (DB auto-increment not relied on).

    Args:
        tg_id: Telegram user ID (optional)
        ds_id: Discord user ID (snowflake, optional)
        nickname: Nickname on server (optional)
        role: Player role (default: GUEST)
        balance: Initial balance (default: 0)
        language: Player language (default: RU)
        ref_father: Referral father player (optional)

    Returns:
        Player: Created player instance with valid .id

    Raises:
        Exception: If creation fails (e.g., duplicate tg_id, ds_id, or nickname)
    """
    # Normalize string fields so lookups (case-insensitive, trim) find them
    if isinstance(nickname, str):
        nickname = nickname.strip() or None
    if isinstance(ds_id, str):
        ds_id = ds_id.strip() or None

    for attempt in range(5):
        player_id = _generate_player_id()
        try:
            player = await Player.create(
                id=player_id,
                tg_id=tg_id,
                ds_id=ds_id,
                nickname=nickname,
                role=role,
                balance=balance,
                language=language,
                ref_father=ref_father,
            )
            _players_log.info(
                "Player created player_id=%s nickname=%s tg_id=%s ds_id=%s",
                player.id,
                nickname,
                tg_id,
                ds_id,
            )
            logger.info(
                "👤 Player created",
                player_id=player.id,
                tg_id=tg_id,
                ds_id=ds_id,
                nickname=nickname,
            )
            return player
        except Exception as e:
            err_str = str(e).lower()
            # Retry only on id (pkey) collision; duplicate tg_id/ds_id/nickname → raise
            is_id_collision = "duplicate" in err_str and (
                "pkey" in err_str or "primary" in err_str or " key " in err_str
            )
            if is_id_collision and attempt < 4:
                continue
            logger.error(
                "Failed to create player",
                error=str(e),
                tg_id=tg_id,
                ds_id=ds_id,
                nickname=nickname,
            )
            raise
    raise RuntimeError("Failed to generate unique player id after retries")


async def get_player(player: Union[int, Player]) -> Optional[Player]:
    """
    Get player by ID или по экземпляру Player.

    Args:
        player: id игрока (int) или экземпляр Player

    Returns:
        Player or None if not found
    """
    try:
        pid = to_id(player)
        return await Player.get_or_none(id=pid)
    except Exception as e:
        logger.error("Failed to get player", error=str(e), player_id=to_id(player))
        raise


async def get_player_by_tg_id(tg_id: int) -> Optional[Player]:
    """
    Get player by Telegram ID

    Args:
        tg_id: Telegram user ID

    Returns:
        Player or None if not found
    """
    try:
        return await Player.get_or_none(tg_id=tg_id)
    except Exception as e:
        logger.error("Failed to get player by tg_id", error=str(e), tg_id=tg_id)
        raise


async def link_telegram(player: Player, tg_id: int) -> Player:
    """
    Link Telegram account to the current player.
    Fails if this tg_id is already linked to another player.

    Args:
        player: Player instance to link
        tg_id: Telegram user ID

    Returns:
        Updated Player instance

    Raises:
        ValueError: If tg_id is already linked to another account
    """
    try:
        existing = await Player.get_or_none(tg_id=tg_id)
        if existing is not None and existing.id != player.id:
            raise ValueError("This Telegram is already linked to another account")
        return await update_player(player, tg_id=tg_id)
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            "Failed to link Telegram",
            error=str(e),
            player_id=player.id,
            tg_id=tg_id,
        )
        raise


async def unlink_telegram(player: Player) -> Player:
    """
    Unlink Telegram account from the current player.
    Sets tg_id to None.

    Args:
        player: Player instance to unlink

    Returns:
        Updated Player instance

    Raises:
        Exception: If update fails
    """
    try:
        previous_tg_id = player.tg_id
        player.tg_id = None
        await player.save(update_fields=["tg_id"])
        logger.info(
            "🔓 Telegram unlinked",
            player_id=player.id,
            previous_tg_id=previous_tg_id,
        )
        return player
    except Exception as e:
        logger.error(
            "Failed to unlink Telegram",
            error=str(e),
            player_id=player.id,
        )
        raise


async def get_player_by_ds_id(ds_id: str) -> Optional[Player]:
    """
    Get player by Discord ID

    Args:
        ds_id: Discord user ID (snowflake)

    Returns:
        Player or None if not found
    """
    try:
        return await Player.get_or_none(ds_id=ds_id)
    except Exception as e:
        logger.error("Failed to get player by ds_id", error=str(e), ds_id=ds_id)
        raise


async def get_player_by_nickname(nickname: str) -> Optional[Player]:
    """
    Get player by nickname (case-insensitive, trim whitespace).

    Tries exact match first, then case-insensitive match so existing players
    are found regardless of client sending different casing.
    """
    if not nickname:
        return None
    nickname_clean = nickname.strip()
    if not nickname_clean:
        return None
    try:
        # Exact match first (fast path)
        player = await Player.get_or_none(nickname=nickname_clean)
        if player:
            return player
        # Case-insensitive fallback: DB may have "Steve", client sent "steve"
        conn = connections.get("default")
        rows = await conn.execute_query_dict(
            "SELECT id FROM player WHERE nickname IS NOT NULL AND LOWER(TRIM(nickname)) = LOWER(TRIM($1)) LIMIT 1",
            [nickname_clean],
        )
        if rows and len(rows) > 0:
            return await Player.get_or_none(id=rows[0]["id"])
        return None
    except Exception as e:
        logger.error(
            "Failed to get player by nickname", error=str(e), nickname=nickname
        )
        raise


async def get_players_by_role(role: PlayerRoles) -> List[Player]:
    """
    Get all players with specific role

    Args:
        role: Player role to filter by

    Returns:
        List of Player instances
    """
    try:
        return await Player.filter(role=role).all()
    except Exception as e:
        logger.error("Failed to get players by role", error=str(e), role=role.value)
        raise


async def get_ref_children(ref_father: Player) -> List[Player]:
    """
    Get all referral children of a player

    Args:
        ref_father: Player who is the referral father

    Returns:
        List of Player instances (referral children)
    """
    try:
        return await Player.filter(ref_father=ref_father).all()
    except Exception as e:
        logger.error(
            "Failed to get ref children", error=str(e), ref_father_id=ref_father.id
        )
        raise


async def get_players(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    role: Optional[PlayerRoles] = None,
    has_banned: Optional[bool] = None,
    has_locked: Optional[bool] = None,
) -> List[Player]:
    """
    Get players with optional filters

    Args:
        limit: Maximum number of players to return
        offset: Number of players to skip
        role: Filter by role (optional)
        has_banned: Filter by banned status (optional)
        has_locked: Filter by locked status (optional)

    Returns:
        List of Player instances
    """
    try:
        query = Player.all()

        if role is not None:
            query = query.filter(role=role)
        if has_banned is not None:
            query = query.filter(has_banned=has_banned)
        if has_locked is not None:
            query = query.filter(has_locked=has_locked)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query
    except Exception as e:
        logger.error("Failed to get players", error=str(e))
        raise


async def update_player(
    player: Player,
    tg_id: Optional[int] = None,
    ds_id: Optional[str] = None,
    nickname: Optional[str] = None,
    role: Optional[PlayerRoles] = None,
    language: Optional[Languages] = None,
    ref_father: Optional[Player] = None,
    has_locked: Optional[bool] = None,
    has_banned: Optional[bool] = None,
) -> Player:
    """
    Update player fields

    Args:
        player: Player instance to update
        tg_id: New Telegram ID (optional)
        ds_id: New Discord ID (optional)
        nickname: New nickname (optional)
        role: New role (optional)
        language: New language (optional)
        ref_father: New referral father (optional, None to remove)
        has_locked: New locked status (optional)
        has_banned: New banned status (optional)

    Returns:
        Updated Player instance

    Raises:
        Exception: If update fails (e.g., duplicate tg_id, ds_id, or nickname)
    """
    try:
        if tg_id is not None:
            player.tg_id = tg_id
        if ds_id is not None:
            player.ds_id = ds_id
        if nickname is not None:
            player.nickname = nickname
        if role is not None:
            player.role = role
        if language is not None:
            player.language = language
        if ref_father is not None or (
            ref_father is None and player.ref_father is not None
        ):
            player.ref_father = ref_father
        if has_locked is not None:
            player.has_locked = has_locked
        if has_banned is not None:
            player.has_banned = has_banned

        await player.save()
        logger.info("🔄 Player updated", player_id=player.id)
        return player
    except Exception as e:
        logger.error("Failed to update player", error=str(e), player_id=player.id)
        raise


async def delete_player(player: Player) -> None:
    """
    Delete player

    Args:
        player: Player instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        player_id = player.id
        await player.delete()
        logger.info("🗑️ Player deleted", player_id=player_id)
    except Exception as e:
        logger.error("Failed to delete player", error=str(e), player_id=player_id)
        raise


async def _get_locked_player(pid: int, conn) -> Player:
    locked = await Player.filter(id=pid).using_db(conn).select_for_update().first()
    if not locked:
        raise ValueError("Player not found")
    return locked


async def increase_player_balance(player: Union[int, Player], amount: int) -> Player:
    """
    Increase player balance atomically (locks the row for the duration).

    Args:
        player: Player instance or id
        amount: Amount to increase

    Returns:
        Freshly locked Player instance (not necessarily the same object passed in)

    Raises:
        ValueError: If amount is negative or player not found
        Exception: If update fails
    """
    amount = validate_amount(amount=amount)
    pid = to_id(player)

    try:
        async with in_transaction() as conn:
            locked = await _get_locked_player(pid, conn)
            locked.balance += amount
            await locked.save(update_fields=["balance"], using_db=conn)
        logger.info(
            "💰 Player balance increased",
            player_id=pid,
            amount=amount,
            new_balance=locked.balance,
        )
        return locked
    except Exception as e:
        logger.error(
            "Failed to increase player balance",
            error=str(e),
            player_id=pid,
        )
        raise


async def decrease_player_balance(player: Union[int, Player], amount: int) -> Player:
    """
    Decrease player balance atomically (locks the row for the duration).

    Args:
        player: Player instance or id
        amount: Amount to decrease

    Returns:
        Freshly locked Player instance (not necessarily the same object passed in)

    Raises:
        ValueError: If amount is negative, exceeds available balance, or player not found
        Exception: If update fails
    """
    amount = validate_amount(amount=amount)
    pid = to_id(player)

    try:
        async with in_transaction() as conn:
            locked = await _get_locked_player(pid, conn)
            available = locked.balance - getattr(locked, "frozen_balance", 0)
            if available < amount:
                raise ValueError("Insufficient balance")
            locked.balance -= amount
            await locked.save(update_fields=["balance"], using_db=conn)
        logger.info(
            "💰 Player balance decreased",
            player_id=pid,
            amount=amount,
            new_balance=locked.balance,
        )
        return locked
    except Exception as e:
        logger.error(
            "Failed to decrease player balance",
            error=str(e),
            player_id=pid,
        )
        raise


async def set_player_balance(player: Union[int, Player], balance: int) -> Player:
    """
    Set player balance to a specific value atomically (locks the row).

    Args:
        player: Player instance or id
        balance: New balance value

    Returns:
        Freshly locked Player instance (not necessarily the same object passed in)

    Raises:
        ValueError: If balance is negative or player not found
        Exception: If update fails
    """
    if balance < 0:
        raise ValueError("Balance must be >= 0")
    pid = to_id(player)

    try:
        async with in_transaction() as conn:
            locked = await _get_locked_player(pid, conn)
            locked.balance = balance
            await locked.save(update_fields=["balance"], using_db=conn)
        logger.info(
            "💰 Player balance set",
            player_id=pid,
            new_balance=balance,
        )
        return locked
    except Exception as e:
        logger.error(
            "Failed to set player balance",
            error=str(e),
            player_id=pid,
        )
        raise


def get_available_balance(player: Player) -> int:
    """Available balance (balance - frozen_balance)."""
    return player.balance - getattr(player, "frozen_balance", 0)


async def freeze_player_balance(
    player: Union[int, Player], amount: int, reason: str = ""
) -> Player:
    """Increase frozen_balance by amount atomically. Fails if available balance would go negative."""
    validate_amount(amount=amount)
    pid = to_id(player)

    async with in_transaction() as conn:
        locked = await _get_locked_player(pid, conn)
        available = get_available_balance(locked)
        if available < amount:
            raise ValueError("Insufficient balance to freeze")
        locked.frozen_balance = getattr(locked, "frozen_balance", 0) + amount
        await locked.save(update_fields=["frozen_balance"], using_db=conn)
    logger.info(
        "Freeze balance",
        player_id=pid,
        amount=amount,
        reason=reason or None,
        frozen_balance=locked.frozen_balance,
    )
    return locked


async def unfreeze_player_balance(player: Union[int, Player], amount: int) -> Player:
    """Decrease frozen_balance by amount atomically."""
    validate_amount(amount=amount)
    pid = to_id(player)

    async with in_transaction() as conn:
        locked = await _get_locked_player(pid, conn)
        current_frozen = getattr(locked, "frozen_balance", 0)
        if amount > current_frozen:
            raise ValueError("Cannot unfreeze more than frozen amount")
        locked.frozen_balance = current_frozen - amount
        await locked.save(update_fields=["frozen_balance"], using_db=conn)
    logger.info(
        "Unfreeze balance",
        player_id=pid,
        amount=amount,
        frozen_balance=locked.frozen_balance,
    )
    return locked


async def ban_player(player: Player) -> Player:
    """
    Ban player

    Args:
        player: Player instance to ban

    Returns:
        Updated Player instance
    """
    try:
        player.has_banned = True
        await player.save()
        logger.info("🚫 Player banned", player_id=player.id)
        return player
    except Exception as e:
        logger.error("Failed to ban player", error=str(e), player_id=player.id)
        raise


async def unban_player(player: Player) -> Player:
    """
    Unban player

    Args:
        player: Player instance to unban

    Returns:
        Updated Player instance
    """
    try:
        player.has_banned = False
        await player.save()
        logger.info("✅ Player unbanned", player_id=player.id)
        return player
    except Exception as e:
        logger.error("Failed to unban player", error=str(e), player_id=player.id)
        raise


async def lock_player(player: Player) -> Player:
    """
    Lock player bot access

    Args:
        player: Player instance to lock

    Returns:
        Updated Player instance
    """
    try:
        player.has_locked = True
        await player.save()
        logger.info("🔒 Player locked", player_id=player.id)
        return player
    except Exception as e:
        logger.error("Failed to lock player", error=str(e), player_id=player.id)
        raise


async def unlock_player(player: Player) -> Player:
    """
    Unlock player bot access

    Args:
        player: Player instance to unlock

    Returns:
        Updated Player instance
    """
    try:
        player.has_locked = False
        await player.save()
        logger.info("🔓 Player unlocked", player_id=player.id)
        return player
    except Exception as e:
        logger.error("Failed to unlock player", error=str(e), player_id=player.id)
        raise


async def change_player_role(player: Player, role: PlayerRoles) -> Player:
    """
    Change player role

    Args:
        player: Player instance
        role: New role

    Returns:
        Updated Player instance
    """
    try:
        player.role = role
        await player.save()
        logger.info("👑 Player role changed", player_id=player.id, new_role=role.value)
        return player
    except Exception as e:
        logger.error("Failed to change player role", error=str(e), player_id=player.id)
        raise


async def change_player_language(player: Player, language: Languages) -> Player:
    """
    Change player language

    Args:
        player: Player instance
        language: New language

    Returns:
        Updated Player instance
    """
    try:
        player.language = language
        await player.save()
        logger.info(
            "🌐 Player language changed",
            player_id=player.id,
            new_language=language.value,
        )
        return player
    except Exception as e:
        logger.error(
            "Failed to change player language", error=str(e), player_id=player.id
        )
        raise


async def set_ref_father(player: Player, ref_father: Optional[Player]) -> Player:
    """
    Set or remove referral father

    Args:
        player: Player instance
        ref_father: Referral father player (None to remove)

    Returns:
        Updated Player instance

    Raises:
        ValueError: If trying to set player as their own referral father
    """
    if ref_father is not None and player.id == ref_father.id:
        raise ValueError("Player cannot be their own referral father")

    try:
        player.ref_father = ref_father
        await player.save()
        logger.info(
            "👨‍👦 Player ref father set",
            player_id=player.id,
            ref_father_id=ref_father.id if ref_father else None,
        )
        return player
    except Exception as e:
        logger.error("Failed to set ref father", error=str(e), player_id=player.id)
        raise


async def bulk_create_players(players_data: List[dict]) -> List[Player]:
    """
    Bulk create players

    Args:
        players_data: List of dictionaries with player data
            Each dict should contain: tg_id, ds_id, nickname, role, balance, language, ref_father

    Returns:
        List of created Player instances

    Raises:
        Exception: If creation fails
    """
    try:
        created_players = []
        for data in players_data:
            player = await create_player(
                tg_id=data.get("tg_id"),
                ds_id=data.get("ds_id"),
                nickname=data.get("nickname"),
                role=data.get("role", PlayerRoles.GUEST),
                balance=data.get("balance", 0),
                language=data.get("language", Languages.RU),
                ref_father=data.get("ref_father"),
            )
            created_players.append(player)
        logger.info("👥 Bulk players created", count=len(created_players))
        return created_players
    except Exception as e:
        logger.error("Failed to bulk create players", error=str(e))
        raise


async def bulk_update_balances(updates: List[tuple]) -> int:
    """
    Bulk update player balances

    Args:
        updates: List of tuples (player_id, amount) or (player, amount)
            Positive amount increases, negative decreases

    Returns:
        Number of updated players

    Raises:
        Exception: If update fails
    """
    try:
        resolved = [(to_id(item[0]), item[1]) for item in updates]
        if not resolved:
            return 0

        player_ids = sorted({pid for pid, _ in resolved})
        updated_count = 0

        async with in_transaction() as conn:
            locked_players = (
                await Player.filter(id__in=player_ids)
                .using_db(conn)
                .select_for_update()
                .all()
            )
            locked_by_id = {int(p.id): p for p in locked_players}

            for pid, amount in resolved:
                locked = locked_by_id.get(pid)
                if not locked:
                    continue

                if amount > 0:
                    locked.balance += amount
                    await locked.save(update_fields=["balance"], using_db=conn)
                    updated_count += 1
                elif amount < 0:
                    available = locked.balance - getattr(locked, "frozen_balance", 0)
                    if available < abs(amount):
                        raise ValueError(f"Insufficient balance for player {pid}")
                    locked.balance -= abs(amount)
                    await locked.save(update_fields=["balance"], using_db=conn)
                    updated_count += 1

        logger.info("💰 Bulk balances updated", count=updated_count)
        return updated_count
    except Exception as e:
        logger.error("Failed to bulk update balances", error=str(e))
        raise


async def search_players(query: str, limit: int = 20) -> List[Player]:
    """
    Search players by nickname, tg_id, or ds_id

    Args:
        query: Search query
        limit: Maximum number of results

    Returns:
        List of matching Player instances
    """
    try:
        # Try to find by exact match first
        if query.isdigit():
            # Try as tg_id
            player = await get_player_by_tg_id(int(query))
            if player:
                return [player]

        # Try as ds_id
        player = await get_player_by_ds_id(query)
        if player:
            return [player]

        # Try as nickname
        player = await get_player_by_nickname(query)
        if player:
            return [player]

        # Search by nickname (partial match, case-insensitive, DB-level)
        return await Player.filter(nickname__icontains=query).limit(limit)
    except Exception as e:
        logger.error("Failed to search players", error=str(e), query=query)
        raise
