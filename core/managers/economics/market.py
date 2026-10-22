"""
Market manager for CRUD operations on MarketItem model
"""

from typing import Optional, List, Union
from core.models.economics.market import MarketItem
from core.models.players.players import Player
from core.shared.logger import logger
from core.shared.utils import to_id
from core.managers.economics.utils import validate_amount


__all__ = [
    "create_market_item",
    "get_market_item",
    "get_market_items_by_seller",
    "get_market_items",
    "update_market_item",
    "delete_market_item",
    "decrease_market_item_quantity",
]


async def create_market_item(
    seller: Player,
    item_id: str,
    name: str,
    desc: str,
    total_price: int,
    quantity: int,
) -> MarketItem:
    """
    Create a new market item

    Args:
        seller: Player who is selling the item
        item_id: ID of item in Minecraft (e.g., minecraft:stone)
        name: Name of the position
        desc: Description of the position
        total_price: Total price of the item
        quantity: Quantity of items

    Returns:
        MarketItem: Created market item instance

    Raises:
        Exception: If creation fails
    """
    try:
        market_item = await MarketItem.create(
            seller=seller,
            item_id=item_id,
            name=name,
            desc=desc,
            total_price=total_price,
            quantity=quantity,
        )
        logger.info(
            "Market item created",
            item_id=item_id,
            seller_id=seller.id,
            market_item_id=market_item.id,
        )
        return market_item
    except Exception as e:
        logger.error("Failed to create market item", error=str(e), item_id=item_id)
        raise


async def get_market_item(item: Union[int, MarketItem]) -> Optional[MarketItem]:
    """
    Get market item by ID или по экземпляру MarketItem.

    Args:
        item: id позиции маркета (int) или экземпляр MarketItem

    Returns:
        MarketItem or None if not found
    """
    try:
        mid = to_id(item)
        return await MarketItem.get_or_none(id=mid)
    except Exception as e:
        logger.error(
            "Failed to get market item", error=str(e), item_id=to_id(item)
        )
        raise


async def get_market_items_by_seller(seller: Player) -> List[MarketItem]:
    """
    Get all market items by seller

    Args:
        seller: Player who is selling

    Returns:
        List of MarketItem instances
    """
    try:
        return await MarketItem.filter(seller=seller).all()
    except Exception as e:
        logger.error(
            "Failed to get market items by seller", error=str(e), seller_id=seller.id
        )
        raise


async def get_market_items(
    item_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
) -> List[MarketItem]:
    """
    Get market items with optional filters

    Args:
        item_id: Minecraft item ID filter (e.g., minecraft:stone)
        limit: Maximum number of items to return
        offset: Number of items to skip
        min_price: Minimum total price filter
        max_price: Maximum total price filter

    Returns:
        List of MarketItem instances
    """
    try:
        query = MarketItem.all()

        if item_id is not None:
            query = query.filter(item_id=item_id)
        if min_price is not None:
            query = query.filter(total_price__gte=min_price)
        if max_price is not None:
            query = query.filter(total_price__lte=max_price)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query
    except Exception as e:
        logger.error("Failed to get market items", error=str(e))
        raise


async def update_market_item(
    market_item: MarketItem,
    name: Optional[str] = None,
    desc: Optional[str] = None,
    total_price: Optional[int] = None,
    quantity: Optional[int] = None,
) -> MarketItem:
    """
    Update market item fields

    Args:
        market_item: MarketItem instance to update
        name: New name (optional)
        desc: New description (optional)
        total_price: New total price (optional)
        quantity: New quantity (optional)

    Returns:
        Updated MarketItem instance

    Raises:
        Exception: If update fails
    """
    try:
        if name is not None:
            market_item.name = name
        if desc is not None:
            market_item.desc = desc
        if total_price is not None:
            market_item.total_price = total_price
        if quantity is not None:
            market_item.quantity = quantity

        await market_item.save()
        logger.info("Market item updated", market_item_id=market_item.id)
        return market_item
    except Exception as e:
        logger.error(
            "Failed to update market item", error=str(e), market_item_id=market_item.id
        )
        raise


async def delete_market_item(market_item: MarketItem) -> None:
    """
    Delete market item

    Args:
        market_item: MarketItem instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        item_id = market_item.id
        await market_item.delete()
        logger.info("Market item deleted", market_item_id=item_id)
    except Exception as e:
        logger.error("Failed to delete market item", error=str(e), item_id=item_id)
        raise


async def decrease_market_item_quantity(
    market_item: MarketItem, amount: int
) -> MarketItem:
    """
    Decrease market item quantity

    Args:
        market_item: MarketItem instance
        amount: Amount to decrease

    Returns:
        Updated MarketItem instance

    Raises:
        ValueError: If amount is negative or exceeds available quantity
        Exception: If update fails
    """
    amount = validate_amount(amount=amount)
    if market_item.quantity < amount:
        raise ValueError("Insufficient quantity")

    try:
        market_item.quantity -= amount
        await market_item.save()
        logger.info(
            "Market item quantity decreased",
            market_item_id=market_item.id,
            amount=amount,
            new_quantity=market_item.quantity,
        )
        return market_item
    except Exception as e:
        logger.error(
            "Failed to decrease market item quantity",
            error=str(e),
            market_item_id=market_item.id,
        )
        raise
