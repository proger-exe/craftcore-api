"""
Clans manager for CRUD operations on Clan model
"""

from typing import Optional, List, Dict, Union, Any
from core.models.social.clans import Clan, ClanRole
from core.models.players.players import Player
from core.shared.db import locked_row
from core.shared.errors import InsufficientBalanceError, NotFoundError, ValidationError
from core.shared.logger import logger
from core.shared.utils import to_id
from core.managers.economics.utils import validate_amount


def normalize_clan_inventory(inventory: List[Any]) -> List[Dict[str, Any]]:
    """
    Normalize clan inventory to list of dicts with item_id, quantity, item_nbt (str).
    Missing item_nbt or non-string -> ""; quantity coerced to int.
    """
    result: List[Dict[str, Any]] = []
    for entry in inventory if isinstance(inventory, list) else []:
        if not isinstance(entry, dict):
            continue
        item_id = entry.get("item_id")
        if item_id is None:
            continue
        try:
            qty = int(entry.get("quantity", 0))
        except (TypeError, ValueError):
            qty = 0
        nbt = entry.get("item_nbt")
        if not isinstance(nbt, str):
            nbt = ""
        result.append({"item_id": str(item_id), "quantity": qty, "item_nbt": nbt})
    return result


async def create_clan(
    owner: Player,
    name: str,
    tag: str,
    description: str = "",
    prefix: str = "",
) -> Clan:
    """
    Create a new clan

    Args:
        owner: Player who owns the clan
        name: Name of the clan (max 32 chars)
        tag: Tag of the clan (max 5 chars)
        description: Description of the clan (default: "")
        prefix: Prefix of the clan (default: "")

    Returns:
        Clan: Created clan instance

    Raises:
        Exception: If creation fails
    """
    try:
        clan = await Clan.create(
            owner_id=owner,
            name=name,
            tag=tag,
            description=description,
            prefix=prefix,
            members=[],
            inventory=[],
            balance=0,
            homes=[],
        )
        logger.info("🏰 Clan created", clan_id=clan.id, owner_id=owner.id, name=name)
        return clan
    except Exception as e:
        logger.error("Failed to create clan", error=str(e), owner_id=owner.id)
        raise


async def get_clan(clan: Union[int, Clan]) -> Optional[Clan]:
    """
    Get clan by ID или по экземпляру Clan.

    Args:
        clan: id клана (int) или экземпляр Clan

    Returns:
        Clan or None if not found
    """
    try:
        cid = to_id(clan)
        return await Clan.get_or_none(id=cid)
    except Exception as e:
        logger.error("Failed to get clan", error=str(e), clan_id=to_id(clan))
        raise


async def get_clans_by_owner(owner: Player) -> List[Clan]:
    """
    Get all clans owned by a player

    Args:
        owner: Player who owns the clans

    Returns:
        List of Clan instances
    """
    try:
        return await Clan.filter(owner_id=owner).all()
    except Exception as e:
        logger.error("Failed to get clans by owner", error=str(e), owner_id=owner.id)
        raise


async def get_clans(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    name: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[Clan]:
    """
    Get clans with optional filters

    Args:
        limit: Maximum number of clans to return
        offset: Number of clans to skip
        name: Filter by name (partial match, optional)
        tag: Filter by tag (exact match, optional)

    Returns:
        List of Clan instances
    """
    try:
        query = Clan.all()

        if name is not None:
            query = query.filter(name__icontains=name)
        if tag is not None:
            query = query.filter(tag=tag)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query
    except Exception as e:
        logger.error("Failed to get clans", error=str(e))
        raise


async def update_clan(
    clan: Clan,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tag: Optional[str] = None,
    prefix: Optional[str] = None,
    inventory: Optional[list] = None,
    homes: Optional[list] = None,
) -> Clan:
    """
    Update clan fields

    Args:
        clan: Clan instance to update
        name: New name (optional)
        description: New description (optional)
        tag: New tag (optional)
        prefix: New prefix (optional)
        inventory: New inventory list (optional)
        homes: New homes list (optional)

    Returns:
        Updated Clan instance
    """
    try:
        if name is not None:
            clan.name = name
        if description is not None:
            clan.description = description
        if tag is not None:
            clan.tag = tag
        if prefix is not None:
            clan.prefix = prefix
        if inventory is not None:
            clan.inventory = normalize_clan_inventory(inventory)
        if homes is not None:
            clan.homes = homes

        await clan.save()
        logger.info("🔄 Clan updated", clan_id=clan.id)
        return clan
    except Exception as e:
        logger.error("Failed to update clan", error=str(e), clan_id=clan.id)
        raise


async def delete_clan(clan: Clan) -> None:
    """
    Delete clan

    Args:
        clan: Clan instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        clan_id = clan.id
        await clan.delete()
        logger.info("🗑️ Clan deleted", clan_id=clan_id)
    except Exception as e:
        logger.error("Failed to delete clan", error=str(e), clan_id=clan_id)
        raise


async def add_clan_member(
    clan: Clan, player: Player, role: ClanRole = ClanRole.MEMBER
) -> Clan:
    """
    Add member to clan

    Args:
        clan: Clan instance
        player: Player to add
        role: Role of the member (default: MEMBER)

    Returns:
        Updated Clan instance

    Raises:
        ValueError: If player is already a member
        Exception: If update fails
    """
    try:
        async with locked_row(Clan, id=clan.id) as locked_clan:
            members = locked_clan.members or []
            # Check if player is already a member
            for member in members:
                if isinstance(member, dict) and member.get("id") == player.id:
                    raise ValidationError("Player is already a member of this clan")
                elif (
                    isinstance(member, list) and len(member) > 0 and member[0] == player.id
                ):
                    raise ValidationError("Player is already a member of this clan")

            members.append({"id": player.id, "role": role.value})
            locked_clan.members = members
            await locked_clan.save(update_fields=["members"])

        logger.info(
            "👥 Clan member added",
            clan_id=locked_clan.id,
            player_id=player.id,
            role=role.value,
        )
        return locked_clan
    except Exception as e:
        logger.error(
            "Failed to add clan member",
            error=str(e),
            clan_id=clan.id,
            player_id=player.id,
        )
        raise


async def remove_clan_member(clan: Clan, player: Player) -> Clan:
    """
    Remove member from clan

    Args:
        clan: Clan instance
        player: Player to remove

    Returns:
        Updated Clan instance

    Raises:
        ValueError: If player is not a member
        Exception: If update fails
    """
    try:
        async with locked_row(Clan, id=clan.id) as locked_clan:
            members = locked_clan.members or []
            original_length = len(members)

            # Remove player from members
            locked_clan.members = [
                member
                for member in members
                if (isinstance(member, dict) and member.get("id") != player.id)
                or (
                    isinstance(member, list)
                    and len(member) > 0
                    and member[0] != player.id
                )
            ]

            if len(locked_clan.members) == original_length:
                raise ValidationError("Player is not a member of this clan")

            await locked_clan.save(update_fields=["members"])

        logger.info("👥 Clan member removed", clan_id=locked_clan.id, player_id=player.id)
        return locked_clan
    except Exception as e:
        logger.error(
            "Failed to remove clan member",
            error=str(e),
            clan_id=clan.id,
            player_id=player.id,
        )
        raise


async def update_clan_member_role(clan: Clan, player: Player, role: ClanRole) -> Clan:
    """
    Update member role in clan

    Args:
        clan: Clan instance
        player: Player whose role to update
        role: New role

    Returns:
        Updated Clan instance

    Raises:
        ValueError: If player is not a member
        Exception: If update fails
    """
    try:
        async with locked_row(Clan, id=clan.id) as locked_clan:
            members = locked_clan.members or []
            found = False

            for i, member in enumerate(members):
                if isinstance(member, dict) and member.get("id") == player.id:
                    members[i] = {"id": player.id, "role": role.value}
                    found = True
                    break
                elif (
                    isinstance(member, list) and len(member) > 0 and member[0] == player.id
                ):
                    members[i] = [player.id, role.value]
                    found = True
                    break

            if not found:
                raise ValidationError("Player is not a member of this clan")

            locked_clan.members = members
            await locked_clan.save(update_fields=["members"])

        logger.info(
            "👑 Clan member role updated",
            clan_id=locked_clan.id,
            player_id=player.id,
            new_role=role.value,
        )
        return locked_clan
    except Exception as e:
        logger.error(
            "Failed to update clan member role",
            error=str(e),
            clan_id=clan.id,
            player_id=player.id,
        )
        raise


async def increase_clan_balance(clan: Clan, amount: int) -> Clan:
    """
    Increase clan balance

    Args:
        clan: Clan instance
        amount: Amount to increase

    Returns:
        Updated Clan instance

    Raises:
        ValueError: If amount is negative
        Exception: If update fails
    """
    amount = validate_amount(amount=amount)

    try:
        async with locked_row(Clan, id=clan.id) as locked_clan:
            locked_clan.balance += amount
            await locked_clan.save(update_fields=["balance"])

        logger.info(
            "💰 Clan balance increased",
            clan_id=locked_clan.id,
            amount=amount,
            new_balance=locked_clan.balance,
        )
        return locked_clan
    except Exception as e:
        logger.error("Failed to increase clan balance", error=str(e), clan_id=clan.id)
        raise


async def decrease_clan_balance(clan: Clan, amount: int) -> Clan:
    """
    Decrease clan balance

    Args:
        clan: Clan instance
        amount: Amount to decrease

    Returns:
        Updated Clan instance

    Raises:
        ValueError: If amount is negative or exceeds available balance
        Exception: If update fails
    """
    amount = validate_amount(amount=amount)

    try:
        async with locked_row(Clan, id=clan.id) as locked_clan:
            if locked_clan.balance < amount:
                raise InsufficientBalanceError("Insufficient balance")
            locked_clan.balance -= amount
            await locked_clan.save(update_fields=["balance"])

        logger.info(
            "💰 Clan balance decreased",
            clan_id=locked_clan.id,
            amount=amount,
            new_balance=locked_clan.balance,
        )
        return locked_clan
    except Exception as e:
        logger.error("Failed to decrease clan balance", error=str(e), clan_id=clan.id)
        raise


async def add_clan_home(
    clan: Clan, home_id: str, name: str, dimension: str, x: float, y: float, z: float
) -> Clan:
    """
    Add home to clan

    Args:
        clan: Clan instance
        home_id: Unique identifier for the home
        name: Name of the home
        dimension: Dimension name
        x: X coordinate
        y: Y coordinate
        z: Z coordinate

    Returns:
        Updated Clan instance

    Raises:
        ValueError: If home_id already exists
        Exception: If update fails
    """
    try:
        async with locked_row(Clan, id=clan.id) as locked_clan:
            homes = locked_clan.homes or []
            # Check if home_id already exists
            for home in homes:
                if isinstance(home, dict) and home.get("id") == home_id:
                    raise ValidationError("Home with this ID already exists")
                elif isinstance(home, list) and len(home) > 0 and home[0] == home_id:
                    raise ValidationError("Home with this ID already exists")

            homes.append({"id": home_id, "name": name, "coords": [dimension, x, y, z]})
            locked_clan.homes = homes
            await locked_clan.save(update_fields=["homes"])

        logger.info("🏠 Clan home added", clan_id=locked_clan.id, home_id=home_id)
        return locked_clan
    except Exception as e:
        logger.error(
            "Failed to add clan home", error=str(e), clan_id=clan.id, home_id=home_id
        )
        raise


async def remove_clan_home(clan: Clan, home_id: str) -> Clan:
    """
    Remove home from clan

    Args:
        clan: Clan instance
        home_id: ID of home to remove

    Returns:
        Updated Clan instance

    Raises:
        ValueError: If home not found
        Exception: If update fails
    """
    try:
        async with locked_row(Clan, id=clan.id) as locked_clan:
            homes = locked_clan.homes or []
            original_length = len(homes)

            locked_clan.homes = [
                home
                for home in homes
                if (isinstance(home, dict) and home.get("id") != home_id)
                or (isinstance(home, list) and len(home) > 0 and home[0] != home_id)
            ]

            if len(locked_clan.homes) == original_length:
                raise NotFoundError("Home not found")

            await locked_clan.save(update_fields=["homes"])

        logger.info("🗑️ Clan home removed", clan_id=locked_clan.id, home_id=home_id)
        return locked_clan
    except Exception as e:
        logger.error(
            "Failed to remove clan home", error=str(e), clan_id=clan.id, home_id=home_id
        )
        raise


async def search_clans(query: str, limit: int = 20) -> List[Clan]:
    """
    Search clans by name

    Args:
        query: Search query
        limit: Maximum number of results

    Returns:
        List of matching Clan instances
    """
    try:
        from core.shared.utils import search_by_name

        all_clans = await Clan.all().limit(limit * 5)  # Get more to filter
        matching = search_by_name(query, all_clans, name_attr="name")
        return matching[:limit]
    except Exception as e:
        logger.error("Failed to search clans", error=str(e), query=query)
        raise
