"""
Party manager for CRUD operations on Party model
"""

from typing import Optional, List, Union
from core.models.social.party import Party, PartyRole
from core.models.players.players import Player
from core.shared.db import locked_row
from core.shared.errors import ValidationError
from core.shared.logger import logger
from core.shared.utils import to_id


async def create_party(leader: Player, name: str) -> Party:
    """
    Create a new party

    Args:
        leader: Player who leads the party
        name: Name of the party (max 32 chars)

    Returns:
        Party: Created party instance

    Raises:
        Exception: If creation fails
    """
    try:
        party = await Party.create(
            leader_id=leader,
            name=name,
            members=[],
        )
        logger.info(
            "🎉 Party created", party_id=party.id, leader_id=leader.id, name=name
        )
        return party
    except Exception as e:
        logger.error("Failed to create party", error=str(e), leader_id=leader.id)
        raise


async def get_party(party: Union[int, Party]) -> Optional[Party]:
    """
    Get party by ID или по экземпляру Party.

    Args:
        party: id пати (int) или экземпляр Party

    Returns:
        Party or None if not found
    """
    try:
        pid = to_id(party)
        return await Party.get_or_none(id=pid)
    except Exception as e:
        logger.error("Failed to get party", error=str(e), party_id=to_id(party))
        raise


async def get_parties_by_leader(leader: Player) -> List[Party]:
    """
    Get all parties led by a player

    Args:
        leader: Player who leads the parties

    Returns:
        List of Party instances
    """
    try:
        return await Party.filter(leader_id=leader).all()
    except Exception as e:
        logger.error(
            "Failed to get parties by leader", error=str(e), leader_id=leader.id
        )
        raise


async def get_parties(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    name: Optional[str] = None,
) -> List[Party]:
    """
    Get parties with optional filters

    Args:
        limit: Maximum number of parties to return
        offset: Number of parties to skip
        name: Filter by name (partial match, optional)

    Returns:
        List of Party instances
    """
    try:
        query = Party.all()

        if name is not None:
            query = query.filter(name__icontains=name)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query
    except Exception as e:
        logger.error("Failed to get parties", error=str(e))
        raise


async def update_party(party: Party, name: Optional[str] = None) -> Party:
    """
    Update party fields

    Args:
        party: Party instance to update
        name: New name (optional)

    Returns:
        Updated Party instance

    Raises:
        Exception: If update fails
    """
    try:
        if name is not None:
            party.name = name

        await party.save()
        logger.info("🔄 Party updated", party_id=party.id)
        return party
    except Exception as e:
        logger.error("Failed to update party", error=str(e), party_id=party.id)
        raise


async def delete_party(party: Party) -> None:
    """
    Delete party

    Args:
        party: Party instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        party_id = party.id
        await party.delete()
        logger.info("🗑️ Party deleted", party_id=party_id)
    except Exception as e:
        logger.error("Failed to delete party", error=str(e), party_id=party_id)
        raise


async def add_party_member(party: Party, player: Player) -> Party:
    """
    Add member to party

    Args:
        party: Party instance
        player: Player to add

    Returns:
        Updated Party instance

    Raises:
        ValueError: If player is already a member or is the leader
        Exception: If update fails
    """
    try:
        # DONT ADD THIS FUCKING SHIT TO THE CODE
        # if party.leader_id.id == player.id:
        #     raise ValueError("Leader cannot be added as a member")

        async with locked_row(Party, id=party.id) as locked_party:
            members = locked_party.members or []
            # Check if player is already a member
            if player.id in members:
                raise ValidationError("Player is already a member of this party")

            members.append(player.id)
            locked_party.members = members
            await locked_party.save(update_fields=["members"])

        logger.info(
            "👥 Party member added", party_id=locked_party.id, player_id=player.id
        )
        return locked_party
    except Exception as e:
        logger.error(
            "Failed to add party member",
            error=str(e),
            party_id=party.id,
            player_id=player.id,
        )
        raise


async def remove_party_member(party: Party, player: Player) -> Party:
    """
    Remove member from party

    Args:
        party: Party instance
        player: Player to remove

    Returns:
        Updated Party instance

    Raises:
        ValueError: If player is not a member
        Exception: If update fails
    """
    try:
        async with locked_row(Party, id=party.id) as locked_party:
            members = locked_party.members or []
            if player.id not in members:
                raise ValidationError("Player is not a member of this party")

            locked_party.members = [
                member_id for member_id in members if member_id != player.id
            ]
            await locked_party.save(update_fields=["members"])

        logger.info(
            "👥 Party member removed", party_id=locked_party.id, player_id=player.id
        )
        return locked_party
    except Exception as e:
        logger.error(
            "Failed to remove party member",
            error=str(e),
            party_id=party.id,
            player_id=player.id,
        )
        raise


async def change_party_leader(party: Party, new_leader: Player) -> Party:
    """
    Change party leader

    Args:
        party: Party instance
        new_leader: New leader player

    Returns:
        Updated Party instance

    Raises:
        ValueError: If new_leader is not a member
        Exception: If update fails
    """
    try:
        async with locked_row(Party, id=party.id) as locked_party:
            await locked_party.fetch_related("leader_id")
            members = locked_party.members or []
            old_leader_id = locked_party.leader_id.id

            # Check if new_leader is a member
            if new_leader.id not in members:
                raise ValidationError("New leader must be a member of the party")

            # Remove new_leader from members and add old leader
            locked_party.members = [
                member_id for member_id in members if member_id != new_leader.id
            ]
            if old_leader_id not in locked_party.members:
                locked_party.members.append(old_leader_id)

            locked_party.leader_id = new_leader
            await locked_party.save()

        logger.info(
            "👑 Party leader changed",
            party_id=locked_party.id,
            old_leader_id=old_leader_id,
            new_leader_id=new_leader.id,
        )
        return locked_party
    except Exception as e:
        logger.error(
            "Failed to change party leader",
            error=str(e),
            party_id=party.id,
            new_leader_id=new_leader.id,
        )
        raise
