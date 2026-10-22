"""
Shops manager for CRUD operations on Shop and ShopItem models
"""

from typing import Optional, List, Union, Any, Dict
from core.models.economics.shops import Shop, ShopItem
from core.models.economics.transactions import Transaction, TransactionType
from core.models.players.players import Player
from core.shared.logger import logger
from core.shared.utils import to_id
from core.managers.economics.utils import validate_amount
from tortoise.transactions import in_transaction


def _shop_id(shop: Union[int, Shop]) -> int:
    """Привести shop к int (id): принимаем int или Shop."""
    if isinstance(shop, int):
        return int(shop)
    if isinstance(shop, Shop):
        return int(shop.id)
    raise TypeError("Expected int or Shop, got %s" % type(shop).__name__)


def _inventory_key(item_id: str, item_nbt: str = "") -> str:
    """Composite key for Shop.inventory: same item_id with different NBT = different slots."""
    nbt = (item_nbt or "").strip()
    return f"{item_id}|{nbt}" if nbt else str(item_id)


def _normalize_inventory(inventory: Any) -> Dict[str, Dict[str, Any]]:
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    if not isinstance(inventory, dict):
        return {}
    normalized: Dict[str, Dict[str, Any]] = {}
    for key, payload in inventory.items():
        if not isinstance(payload, dict):
            continue
        normalized[str(key)] = {
            "price": _safe_int(payload.get("price", 0), 0),
            "quantity": _safe_int(payload.get("quantity", 1), 1),
            "total_count": _safe_int(payload.get("total_count", 0), 0),
            "nbt": (
                payload.get("nbt", "") if isinstance(payload.get("nbt"), str) else ""
            ),
        }
    return normalized


async def _sync_item_to_inventory(
    shop: Shop, shop_item: ShopItem, using_db=None
) -> None:
    inventory = _normalize_inventory(shop.inventory)
    item_nbt = getattr(shop_item, "item_nbt", "") or ""
    key = _inventory_key(shop_item.item_id, item_nbt)
    inventory[key] = {
        "price": int(shop_item.price),
        "quantity": int(shop_item.quantity),
        "total_count": int(shop_item.total_count),
        "nbt": item_nbt,
    }
    shop.inventory = inventory
    await shop.save(update_fields=["inventory"], using_db=using_db)


async def _remove_item_from_inventory(
    shop: Shop, item_id: str, item_nbt: str = "", using_db=None
) -> None:
    inventory = _normalize_inventory(shop.inventory)
    key = _inventory_key(item_id, item_nbt)
    inventory.pop(key, None)
    shop.inventory = inventory
    await shop.save(update_fields=["inventory"], using_db=using_db)


# Shop CRUD operations


async def create_shop(owner: Player, name: str = "Shop") -> Shop:
    """
    Create a new shop

    Args:
        owner: Player who owns the shop
        name: Name of the shop (default: "Shop")

    Returns:
        Shop: Created shop instance

    Raises:
        Exception: If creation fails
    """
    try:
        shop = await Shop.create(owner_id=owner, name=name, inventory={})
        logger.info("Shop created", shop_id=shop.id, owner_id=owner.id, name=name)
        return shop
    except Exception as e:
        logger.error("Failed to create shop", error=str(e), owner_id=owner.id)
        raise


async def get_shop(shop: Union[int, Shop]) -> Optional[Shop]:
    """
    Get shop by ID или по экземпляру Shop.

    Args:
        shop: id магазина (int) или экземпляр Shop

    Returns:
        Shop or None if not found
    """
    try:
        sid = _shop_id(shop)
        return await Shop.get_or_none(id=sid)
    except Exception as e:
        logger.error("Failed to get shop", error=str(e), shop=shop)
        raise


async def get_shops_by_owner(owner: Player) -> List[Shop]:
    """
    Get all shops owned by a player

    Args:
        owner: Player who owns the shops

    Returns:
        List of Shop instances
    """
    try:
        return await Shop.filter(owner_id=owner).all()
    except Exception as e:
        logger.error("Failed to get shops by owner", error=str(e), owner_id=owner.id)
        raise


async def update_shop(shop: Shop, name: Optional[str] = None) -> Shop:
    """
    Update shop fields

    Args:
        shop: Shop instance to update
        name: New name (optional)

    Returns:
        Updated Shop instance

    Raises:
        Exception: If update fails
    """
    try:
        if name is not None:
            shop.name = name

        await shop.save()
        logger.info("Shop updated", shop_id=shop.id)
        return shop
    except Exception as e:
        logger.error("Failed to update shop", error=str(e), shop_id=shop.id)
        raise


async def delete_shop(shop: Shop) -> None:
    """
    Delete shop (cascades to shop items)

    Args:
        shop: Shop instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        shop_id = shop.id
        await shop.delete()
        logger.info("🗑️ Shop deleted", shop_id=shop_id)
    except Exception as e:
        logger.error("Failed to delete shop", error=str(e), shop_id=shop_id)
        raise


# ShopItem CRUD operations


async def create_shop_item(
    shop: Shop,
    item_id: str,
    price: int = 0,
    quantity: int = 1,
    total_count: int = 0,
    item_nbt: str = "",
) -> ShopItem:
    """
    Create a new shop item

    Args:
        shop: Shop instance
        item_id: ID of item in Minecraft (e.g., minecraft:stone)
        price: Price per unit (default: 0)
        quantity: Lot size (default: 1)
        total_count: Total stock in shop (default: 0)
        item_nbt: NBT data (e.g. JSON string); empty = no NBT (default: "")

    Returns:
        ShopItem: Created shop item instance

    Raises:
        Exception: If creation fails (e.g., duplicate (item_id, item_nbt) in shop)
    """
    try:
        validate_amount(amount=price)
        validate_amount(amount=total_count)
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        nbt = (item_nbt or "").strip()

        shop_item = await ShopItem.create(
            shop=shop,
            item_id=item_id,
            item_nbt=nbt,
            price=price,
            quantity=quantity,
            total_count=total_count,
        )
        await _sync_item_to_inventory(shop, shop_item)
        logger.info(
            "🆕 Shop item created",
            shop_item_id=shop_item.id,
            shop_id=shop.id,
            item_id=item_id,
        )
        return shop_item
    except Exception as e:
        logger.error(
            "Failed to create shop item",
            error=str(e),
            shop_id=shop.id,
            item_id=item_id,
        )
        raise


async def get_shop_item(shop_item: Union[int, ShopItem]) -> Optional[ShopItem]:
    """
    Get shop item by ID или по экземпляру ShopItem.

    Args:
        shop_item: id товара (int) или экземпляр ShopItem

    Returns:
        ShopItem or None if not found
    """
    try:
        sid = to_id(shop_item)
        return await ShopItem.get_or_none(id=sid)
    except Exception as e:
        logger.error(
            "Failed to get shop item",
            error=str(e),
            shop_item_id=to_id(shop_item),
        )
        raise


async def get_shop_items(shop: Union[int, Shop]) -> List[ShopItem]:
    """
    Получить все товары одного магазина по ID или по экземпляру Shop.

    Args:
        shop: id магазина (int) или экземпляр Shop

    Returns:
        Список экземпляров ShopItem, принадлежащих магазину
    """
    try:
        sid = _shop_id(shop)
        return await ShopItem.filter(shop_id=sid, total_count__gt=0).all()
    except Exception as e:
        logger.error(
            "Не удалось получить товары магазина по ID", error=str(e), shop_id=shop
        )
        raise


async def get_shop_item_by_shop_and_item_id(
    shop: Shop, item_id: str, item_nbt: str = ""
) -> Optional[ShopItem]:
    """
    Get shop item by shop, item_id and optional item_nbt.

    Args:
        shop: Shop instance
        item_id: ID of item in Minecraft
        item_nbt: NBT data; empty = no NBT (default: "")

    Returns:
        ShopItem or None if not found
    """
    try:
        nbt = (item_nbt or "").strip()
        return await ShopItem.get_or_none(shop=shop, item_id=item_id, item_nbt=nbt)
    except Exception as e:
        logger.error(
            "Failed to get shop item by shop and item_id",
            error=str(e),
            shop_id=shop.id,
            item_id=item_id,
        )
        raise


async def get_shop_items_by_shop(shop: Shop) -> List[ShopItem]:
    """
    Get all items in a shop

    Args:
        shop: Shop instance

    Returns:
        List of ShopItem instances
    """
    try:
        return await ShopItem.filter(shop=shop).all()
    except Exception as e:
        logger.error("Failed to get shop items by shop", error=str(e), shop_id=shop.id)
        raise


async def get_shop_items_by_item_id(item_id: str) -> List[ShopItem]:
    """
    Get all shop items by Minecraft item ID across all shops

    Args:
        item_id: ID of item in Minecraft (e.g., minecraft:stone)

    Returns:
        List of ShopItem instances
    """
    try:
        return await ShopItem.filter(item_id=item_id).all()
    except Exception as e:
        logger.error(
            "Failed to get shop items by item_id", error=str(e), item_id=item_id
        )
        raise


async def sync_shop_items_full(
    shop: Shop,
    items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Full sync of shop items with source of truth (e.g., Minecraft).
    Existing rows are updated by item_id, missing rows are deleted, new rows are created.
    """
    if items is None:
        raise ValueError("Items payload is required")

    prepared_items: List[Dict[str, Any]] = []
    seen_keys: set = set()
    for raw in items:
        item_id = str(raw.get("item_id", "")).strip()
        if not item_id:
            raise ValueError("item_id is required for each item")
        item_nbt = str(raw.get("item_nbt", "") or "").strip()
        key = (item_id, item_nbt)
        if key in seen_keys:
            raise ValueError(f"Duplicate (item_id, item_nbt) in payload: {key}")
        seen_keys.add(key)

        price = validate_amount(amount=int(raw.get("price", 0)))
        quantity = int(raw.get("quantity", 1))
        total_count = validate_amount(amount=int(raw.get("total_count", 0)))
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        if total_count < quantity:
            raise ValueError("total_count cannot be less than quantity")

        prepared_items.append(
            {
                "item_id": item_id,
                "item_nbt": item_nbt,
                "price": price,
                "quantity": quantity,
                "total_count": total_count,
            }
        )

    created = 0
    updated = 0
    deleted = 0

    async with in_transaction() as conn:
        locked_shop = (
            await Shop.filter(id=shop.id).using_db(conn).select_for_update().first()
        )
        if not locked_shop:
            raise ValueError("Shop not found")

        existing_items = (
            await ShopItem.filter(shop_id=locked_shop.id)
            .using_db(conn)
            .select_for_update()
            .all()
        )
        existing_by_key = {
            (it.item_id, (getattr(it, "item_nbt", None) or "")): it
            for it in existing_items
        }
        incoming_keys = {(it["item_id"], it["item_nbt"]) for it in prepared_items}

        # Upsert by (item_id, item_nbt): update existing, create missing.
        for it in prepared_items:
            key = (it["item_id"], it["item_nbt"])
            existing = existing_by_key.get(key)
            if existing:
                changed_fields = []
                if existing.price != it["price"]:
                    existing.price = it["price"]
                    changed_fields.append("price")
                if existing.quantity != it["quantity"]:
                    existing.quantity = it["quantity"]
                    changed_fields.append("quantity")
                new_total = it["total_count"]
                if existing.total_count != new_total:
                    existing.total_count = new_total
                    changed_fields.append("total_count")

                if changed_fields:
                    await existing.save(update_fields=changed_fields, using_db=conn)
                    updated += 1
            else:
                created_item = await ShopItem.create(
                    shop=locked_shop,
                    item_id=it["item_id"],
                    item_nbt=it["item_nbt"],
                    price=it["price"],
                    quantity=it["quantity"],
                    total_count=it["total_count"],
                    using_db=conn,
                )
                existing_by_key[(created_item.item_id, created_item.item_nbt or "")] = (
                    created_item
                )
                created += 1

        # Delete ghost items that are absent in incoming payload.
        for key, existing in list(existing_by_key.items()):
            if key not in incoming_keys:
                await existing.delete(using_db=conn)
                deleted += 1
                existing_by_key.pop(key, None)

        # Rebuild inventory mirror from resulting DB state.
        final_items = list(existing_by_key.values())
        inventory = {}
        for it in final_items:
            inv_key = _inventory_key(it.item_id, getattr(it, "item_nbt", "") or "")
            inventory[inv_key] = {
                "price": int(it.price),
                "quantity": int(it.quantity),
                "total_count": int(it.total_count),
                "nbt": getattr(it, "item_nbt", "") or "",
            }
        locked_shop.inventory = inventory
        await locked_shop.save(update_fields=["inventory"], using_db=conn)

    logger.info(
        "🔄 Full shop items sync completed",
        shop_id=shop.id,
        created=created,
        updated=updated,
        deleted=deleted,
        total=len(prepared_items),
    )
    return {
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "total": len(prepared_items),
        "items": list(existing_by_key.values()),
    }


async def update_shop_item(
    shop_item: ShopItem,
    price: Optional[int] = None,
    quantity: Optional[int] = None,
    total_count: Optional[int] = None,
    item_nbt: Optional[str] = None,
) -> ShopItem:
    """
    Update shop item fields

    Args:
        shop_item: ShopItem instance to update
        price: New price per unit (optional)
        quantity: New lot size (optional)
        total_count: New total stock (optional)
        item_nbt: New NBT data; empty string = no NBT (optional)

    Returns:
        Updated ShopItem instance

    Raises:
        ValueError: If price or quantity is negative
        Exception: If update fails
    """
    try:
        update_fields: List[str] = []
        # Remember original values to validate cross-field constraints later
        original_quantity = shop_item.quantity
        original_total = shop_item.total_count

        old_nbt = (getattr(shop_item, "item_nbt", None) or "").strip()
        if item_nbt is not None:
            new_nbt = (item_nbt or "").strip()
            shop_item.item_nbt = new_nbt
            update_fields.append("item_nbt")

        if price is not None:
            validate_amount(amount=price)
            shop_item.price = price
            update_fields.append("price")

        if quantity is not None:
            if quantity < 1:
                raise ValueError("Quantity must be at least 1")
            shop_item.quantity = quantity
            update_fields.append("quantity")

        if total_count is not None:
            validate_amount(amount=total_count)
            shop_item.total_count = total_count
            update_fields.append("total_count")

        # Cross-field validation: total_count cannot be less than quantity
        new_quantity = shop_item.quantity if quantity is not None else original_quantity
        new_total = (
            shop_item.total_count if total_count is not None else original_total
        )
        if new_total < new_quantity:
            raise ValueError("total_count cannot be less than quantity")

        if update_fields:
            await shop_item.save(update_fields=update_fields)
        await shop_item.fetch_related("shop")
        shop = shop_item.shop
        if item_nbt is not None and old_nbt != ((item_nbt or "").strip()):
            await _remove_item_from_inventory(shop, shop_item.item_id, old_nbt)
        await _sync_item_to_inventory(shop, shop_item)
        logger.info("🔄 Shop item updated", shop_item_id=shop_item.id)
        return shop_item

    except Exception as e:
        logger.error(
            "Failed to update shop item", error=str(e), shop_item_id=shop_item.id
        )
        raise


async def delete_shop_item(shop_item: ShopItem) -> None:
    """
    Delete shop item

    Args:
        shop_item: ShopItem instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        await shop_item.fetch_related("shop")
        shop = shop_item.shop
        shop_item_id = shop_item.id
        item_id = shop_item.item_id
        item_nbt = (getattr(shop_item, "item_nbt", None) or "").strip()
        await shop_item.delete()
        await _remove_item_from_inventory(shop, item_id, item_nbt)
        logger.info("Shop item deleted", shop_item_id=shop_item_id)

    except Exception as e:
        logger.error(
            "Failed to delete shop item", error=str(e), shop_item_id=shop_item_id
        )
        raise


async def increase_shop_item_quantity(shop_item: ShopItem, amount: int) -> ShopItem:
    """
    Increase total stock for a shop item.

    Args:
        shop_item: ShopItem instance
        amount: Amount to increase

    Returns:
        Updated ShopItem instance

    Raises:
        ValueError: If amount is negative
        Exception: If update fails
    """
    amount = validate_amount(amount=amount)
    if amount < 1:
        raise ValueError("Amount must be at least 1")

    try:
        shop_item.total_count += amount
        await shop_item.save(update_fields=["total_count"])
        await shop_item.fetch_related("shop")
        await _sync_item_to_inventory(shop_item.shop, shop_item)
        logger.info(
            "🔼 Shop item total_count increased",
            shop_item_id=shop_item.id,
            amount=amount,
            new_total_count=shop_item.total_count,
        )
        return shop_item

    except Exception as e:
        logger.error(
            "Failed to increase shop item quantity",
            error=str(e),
            shop_item_id=shop_item.id,
        )
        raise


async def decrease_shop_item_quantity(shop_item: ShopItem, amount: int) -> ShopItem:
    """
    Decrease total stock for a shop item.
    """
    amount = validate_amount(amount=amount)
    if amount < 1:
        raise ValueError("Amount must be at least 1")
    try:
        rows = await ShopItem.filter(id=shop_item.id).values("total_count")
        if not rows:
            raise ValueError("Shop item not found")
        current = rows[0]["total_count"]
        if current < amount:
            raise ValueError("Insufficient quantity in shop")
        new_total_count = current - amount
        await ShopItem.filter(id=shop_item.id).update(total_count=new_total_count)
        shop_item.total_count = new_total_count
        await shop_item.fetch_related("shop")
        await _sync_item_to_inventory(shop_item.shop, shop_item)
        logger.info(
            "🔽 Shop item total_count decreased",
            shop_item_id=shop_item.id,
            amount=amount,
            new_total_count=new_total_count,
        )
        return shop_item
    except ValueError:
        raise
    except Exception as e:
        logger.error(
            "Failed to decrease shop item quantity",
            error=str(e),
            shop_item_id=shop_item.id,
        )
        raise


async def buy_shop_item(buyer: Player, shop_item: ShopItem, quantity: int) -> ShopItem:
    """
    Buy item from shop: check balance, transfer money to owner, decrease total_count.

    Args:
        buyer: Player who buys
        shop_item: ShopItem instance
        quantity: Amount to buy

    Returns:
        Updated ShopItem instance

    Raises:
        ValueError: Insufficient balance, insufficient quantity, or invalid amount
    """
    quantity = validate_amount(amount=quantity)
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")

    async with in_transaction() as conn:
        locked_item = (
            await ShopItem.filter(id=shop_item.id)
            .using_db(conn)
            .select_for_update()
            .first()
        )
        if not locked_item:
            raise ValueError("Shop item not found")
        if locked_item.total_count < quantity:
            raise ValueError("Insufficient quantity in shop")

        locked_shop = (
            await Shop.filter(id=locked_item.shop_id)
            .using_db(conn)
            .select_for_update()
            .first()
        )
        if not locked_shop:
            raise ValueError("Shop not found")
        await locked_shop.fetch_related("owner_id")
        owner = locked_shop.owner_id

        locked_buyer = (
            await Player.filter(id=buyer.id).using_db(conn).select_for_update().first()
        )
        if not locked_buyer:
            raise ValueError("Buyer not found")
        locked_owner = (
            await Player.filter(id=owner.id).using_db(conn).select_for_update().first()
        )
        if not locked_owner:
            raise ValueError("Owner not found")

        total = locked_item.price * quantity
        is_self_purchase = locked_buyer.id == locked_owner.id
        if not is_self_purchase:
            available_buyer = locked_buyer.balance - getattr(
                locked_buyer, "frozen_balance", 0
            )
            if available_buyer < total:
                raise ValueError("Insufficient balance")
            locked_buyer.balance -= total
            locked_owner.balance += total

        locked_item.total_count -= quantity

        if not is_self_purchase:
            await locked_buyer.save(update_fields=["balance"], using_db=conn)
            await locked_owner.save(update_fields=["balance"], using_db=conn)
        await locked_item.save(update_fields=["total_count"], using_db=conn)
        await _sync_item_to_inventory(locked_shop, locked_item, using_db=conn)
        await Transaction.create(
            from_player=locked_buyer,
            to_player=locked_owner,
            amount=total,
            transaction_type=TransactionType.PURCHASE,
            description=(
                f"Shop purchase: {locked_item.item_id} x{quantity} from shop "
                f"{locked_shop.id}"
            ),
            related_entity_type="shop_item",
            related_entity_id=locked_item.id,
            using_db=conn,
        )

    shop_item.total_count = locked_item.total_count
    shop_item.price = locked_item.price
    shop_item.quantity = locked_item.quantity

    logger.info(
        "🛒 Shop item bought",
        shop_item_id=shop_item.id,
        buyer_id=locked_buyer.id,
        owner_id=locked_owner.id,
        quantity=quantity,
        total=total,
    )
    return shop_item
