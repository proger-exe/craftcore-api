"""
Crafts manager for CRUD operations on Craft model
"""

from typing import Optional, List, Dict, Union
from core.models.players.players import Player
from core.models.qol.crafts import Craft
from core.shared.logger import logger
from core.shared.utils import to_id


async def create_craft(
    icon: str,
    name: str,
    description: str = "",
    recipe: Optional[List] = None,
) -> Craft:
    """
    Create a new craft

    Args:
        icon: Icon URL (max 128 chars)
        name: Craft name (max 32 chars)
        description: Craft description (default: empty string)
        recipe: Recipe list (default: empty list)

    Returns:
        Craft: Created craft instance

    Raises:
        Exception: If creation fails
    """
    try:
        craft = await Craft.create(
            icon=icon,
            name=name,
            description=description,
            recipe=recipe or [],
        )
        logger.info("🔨 Craft created", craft_id=craft.id, name=name)
        return craft
    except Exception as e:
        logger.error("Failed to create craft", error=str(e), name=name)
        raise


async def get_craft(craft: Union[int, Craft]) -> Optional[Craft]:
    """
    Get craft by ID или по экземпляру Craft.

    Args:
        craft: id крафта (int) или экземпляр Craft

    Returns:
        Craft or None if not found
    """
    try:
        cid = to_id(craft)
        return await Craft.get_or_none(id=cid)
    except Exception as e:
        logger.error("Failed to get craft", error=str(e), craft_id=to_id(craft))
        raise


async def get_all_crafts(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Craft]:
    """
    Get all crafts

    Args:
        limit: Maximum number of crafts to return
        offset: Number of crafts to skip

    Returns:
        List of Craft instances
    """
    try:
        query = Craft.all()

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error("Failed to get all crafts", error=str(e))
        raise


async def get_craft_by_name(name: str) -> Optional[Craft]:
    """
    Get craft by name

    Args:
        name: Craft name

    Returns:
        Craft or None if not found
    """
    try:
        return await Craft.get_or_none(name=name)
    except Exception as e:
        logger.error("Failed to get craft by name", error=str(e), name=name)
        raise


async def update_craft(
    craft: Craft,
    icon: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    recipe: Optional[List] = None,
) -> Craft:
    """
    Update craft fields

    Args:
        craft: Craft instance to update
        icon: New icon URL (optional)
        name: New name (optional)
        description: New description (optional)
        recipe: New recipe (optional)

    Returns:
        Updated Craft instance

    Raises:
        Exception: If update fails
    """
    try:
        if icon is not None:
            craft.icon = icon
        if name is not None:
            craft.name = name
        if description is not None:
            craft.description = description
        if recipe is not None:
            craft.recipe = recipe

        await craft.save()
        logger.info("🔄 Craft updated", craft_id=craft.id)
        return craft
    except Exception as e:
        logger.error("Failed to update craft", error=str(e), craft_id=craft.id)
        raise


async def delete_craft(craft: Craft) -> None:
    """
    Delete craft

    Args:
        craft: Craft instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        craft_id = craft.id
        await craft.delete()
        logger.info("🗑️ Craft deleted", craft_id=craft_id)
    except Exception as e:
        logger.error("Failed to delete craft", error=str(e), craft_id=craft_id)
        raise


async def get_crafts_by_item(item_id: str) -> List[Craft]:
    """
    Get crafts that use a specific item in recipe

    Args:
        item_id: Item ID to search for (e.g., minecraft:stone)

    Returns:
        List of Craft instances that use this item
    """
    try:
        from core.shared.validators import validate_item_id

        validate_item_id(item_id)

        all_crafts = await get_all_crafts()
        matching = []

        for craft in all_crafts:
            if not craft.recipe:
                continue

            for recipe_item in craft.recipe:
                if (
                    isinstance(recipe_item, dict)
                    and recipe_item.get("item_id") == item_id
                ):
                    matching.append(craft)
                    break

        return matching
    except Exception as e:
        logger.error("Failed to get crafts by item", error=str(e), item_id=item_id)
        raise


async def can_craft(craft: Craft, player: Player) -> bool:
    """
    Check if player can craft this item (has required items in inventory)

    Args:
        craft: Craft instance
        player: Player instance

    Returns:
        True if player can craft, False otherwise

    Note:
        This is a basic check. In real implementation, would check player's actual inventory
    """
    try:
        from core.models.players.players import PlayerProfile

        profile = await PlayerProfile.get_or_none(player=player)
        if not profile or not profile.inventory:
            return False

        # Check if player has all required items
        for recipe_item in craft.recipe:
            if not isinstance(recipe_item, dict):
                continue

            required_item_id = recipe_item.get("item_id")
            required_quantity = recipe_item.get("quantity", 1)

            # Check inventory (assuming inventory is dict: {item_id: quantity})
            player_quantity = profile.inventory.get(required_item_id, 0)
            if player_quantity < required_quantity:
                return False

        return True
    except Exception as e:
        logger.error(
            "Failed to check if can craft",
            error=str(e),
            craft_id=craft.id,
            player_id=player.id,
        )
        raise
