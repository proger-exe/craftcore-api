"""
NPCs manager for CRUD operations on NPC model
"""

from typing import Optional, List, Dict, Union
from core.models.qol.npcs import NPC
from core.shared.logger import logger
from core.shared.utils import to_id


async def create_npc(
    name: str,
    description: str = "",
    locate: Optional[List] = None,
    dialog: Optional[Dict] = None,
    skin: str = "",
) -> NPC:
    """
    Create a new NPC

    Args:
        name: NPC name (max 32 chars)
        description: NPC description (default: empty string)
        locate: Location [dim, x, y, z] (default: empty list)
        dialog: Dialog dict {message_id: message_text} (default: empty dict)
        skin: Skin URL (max 128 chars, default: empty string)

    Returns:
        NPC: Created NPC instance

    Raises:
        Exception: If creation fails
    """
    try:
        npc = await NPC.create(
            name=name,
            description=description,
            locate=locate or [],
            dialog=dialog or {},
            skin=skin,
        )
        logger.info("👤 NPC created", npc_id=npc.id, name=name)
        return npc
    except Exception as e:
        logger.error("Failed to create NPC", error=str(e), name=name)
        raise


async def get_npc(npc: Union[int, NPC]) -> Optional[NPC]:
    """
    Get NPC by ID или по экземпляру NPC.

    Args:
        npc: id NPC (int) или экземпляр NPC

    Returns:
        NPC or None if not found
    """
    try:
        nid = to_id(npc)
        return await NPC.get_or_none(id=nid)
    except Exception as e:
        logger.error("Failed to get NPC", error=str(e), npc_id=to_id(npc))
        raise


async def get_all_npcs(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[NPC]:
    """
    Get all NPCs

    Args:
        limit: Maximum number of NPCs to return
        offset: Number of NPCs to skip

    Returns:
        List of NPC instances
    """
    try:
        query = NPC.all()

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error("Failed to get all NPCs", error=str(e))
        raise


async def get_npc_by_name(name: str) -> Optional[NPC]:
    """
    Get NPC by name

    Args:
        name: NPC name

    Returns:
        NPC or None if not found
    """
    try:
        return await NPC.get_or_none(name=name)
    except Exception as e:
        logger.error("Failed to get NPC by name", error=str(e), name=name)
        raise


async def update_npc(
    npc: NPC,
    name: Optional[str] = None,
    description: Optional[str] = None,
    locate: Optional[List] = None,
    dialog: Optional[Dict] = None,
    skin: Optional[str] = None,
) -> NPC:
    """
    Update NPC fields

    Args:
        npc: NPC instance to update
        name: New name (optional)
        description: New description (optional)
        locate: New location (optional)
        dialog: New dialog (optional)
        skin: New skin URL (optional)

    Returns:
        Updated NPC instance

    Raises:
        Exception: If update fails
    """
    try:
        if name is not None:
            npc.name = name
        if description is not None:
            npc.description = description
        if locate is not None:
            npc.locate = locate
        if dialog is not None:
            npc.dialog = dialog
        if skin is not None:
            npc.skin = skin

        await npc.save()
        logger.info("🔄 NPC updated", npc_id=npc.id)
        return npc
    except Exception as e:
        logger.error("Failed to update NPC", error=str(e), npc_id=npc.id)
        raise


async def delete_npc(npc: NPC) -> None:
    """
    Delete NPC

    Args:
        npc: NPC instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        npc_id = npc.id
        await npc.delete()
        logger.info("🗑️ NPC deleted", npc_id=npc_id)
    except Exception as e:
        logger.error("Failed to delete NPC", error=str(e), npc_id=npc_id)
        raise


async def get_npcs_by_location(
    dim: str, x: float, y: float, z: float, radius: float = 10.0
) -> List[NPC]:
    """
    Get NPCs by location with radius

    Args:
        dim: Dimension name
        x: X coordinate
        y: Y coordinate
        z: Z coordinate
        radius: Search radius (default: 10.0)

    Returns:
        List of NPC instances within radius
    """
    try:
        from core.shared.validators import validate_coordinates

        all_npcs = await NPC.all()
        matching = []

        for npc in all_npcs:
            if not npc.locate or len(npc.locate) != 4:
                continue

            npc_dim, npc_x, npc_y, npc_z = npc.locate

            # Check dimension match
            if npc_dim != dim:
                continue

            # Calculate distance
            distance = ((npc_x - x) ** 2 + (npc_y - y) ** 2 + (npc_z - z) ** 2) ** 0.5

            if distance <= radius:
                matching.append(npc)

        return matching
    except Exception as e:
        logger.error(
            "Failed to get NPCs by location",
            error=str(e),
            dim=dim,
            x=x,
            y=y,
            z=z,
        )
        raise


async def get_npc_dialog_by_id(npc: Union[int, NPC], message_id: str) -> Optional[str]:
    """
    Get NPC dialog text by message ID.

    Args:
        npc: id NPC (int) или экземпляр NPC
        message_id: Message ID to get

    Returns:
        Dialog text or None if not found
    """
    try:
        if isinstance(npc, int):
            npc = await get_npc(npc)
        if not npc:
            return None
        if not npc.dialog or not isinstance(npc.dialog, dict):
            return None

        return npc.dialog.get(message_id)
    except Exception as e:
        try:
            nid = to_id(npc) if npc is not None else None
        except Exception:
            nid = None
        logger.error(
            "Failed to get NPC dialog by ID",
            error=str(e),
            npc_id=nid,
            message_id=message_id,
        )
        raise
