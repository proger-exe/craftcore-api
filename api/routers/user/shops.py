"""
User shops router
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from api.schemas.shops import (
    ShopCreate,
    ShopResponse,
    ShopUpdate,
    ShopItemCreate,
    ShopItemResponse,
    ShopItemUpdate,
    ShopItemBuy,
    ShopItemsFullSyncRequest,
    ShopItemsFullSyncResponse,
    ShopPurchaseResponse,
    ShopWithItemsResponse,
)
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player, validate_pagination
from core.models.players.players import Player
from core.managers.economics.shops import (
    create_shop,
    get_shop,
    get_shops_by_owner,
    update_shop,
    delete_shop,
    create_shop_item,
    get_shop_item,
    get_shop_items,
    update_shop_item,
    delete_shop_item,
    buy_shop_item,
    sync_shop_items_full,
)
from core.managers.players.players import get_player as get_player_by_id
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "shops"])


@router.post("/shops", response_model=ShopResponse, status_code=201)
async def create_shop_endpoint(
    shop_data: ShopCreate, player: Player = Depends(get_current_player)
):
    """Create a new shop"""
    try:
        shop = await create_shop(owner=player, name=shop_data.name)
        await shop.fetch_related("owner_id")
        return ShopResponse(id=shop.id, owner_id=shop.owner_id.id, name=shop.name)
    except Exception as e:
        logger.error("Failed to create shop via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shops", response_model=List[ShopResponse])
async def get_shops_endpoint(
    owner_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get shops"""
    try:
        pagination = validate_pagination(page=page, per_page=per_page)

        if owner_id:
            owner = await get_player_by_id(owner_id)
            if not owner:
                raise HTTPException(status_code=404, detail="Owner not found")
            shops = await get_shops_by_owner(owner)
        else:
            shops = await get_shops_by_owner(player)

        for s in shops:
            await s.fetch_related("owner_id")
        return [
            ShopResponse(id=s.id, owner_id=s.owner_id.id, name=s.name) for s in shops
        ]
    except Exception as e:
        logger.error("Failed to get shops via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shops/{shop_id}", response_model=ShopWithItemsResponse)
async def get_shop_endpoint(shop_id: int, player: Player = Depends(get_current_player)):
    """Get shop by ID with items"""
    try:
        shop = await get_shop(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        await shop.fetch_related("owner_id")
        items = await get_shop_items(shop)
        shop_data = ShopResponse(id=shop.id, owner_id=shop.owner_id.id, name=shop.name)
        return ShopWithItemsResponse(
            **shop_data.model_dump(),
            items=[ShopItemResponse.model_validate(i) for i in items],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get shop via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/shops/{shop_id}", response_model=ShopResponse)
async def update_shop_endpoint(
    shop_id: int,
    shop_data: ShopUpdate,
    player: Player = Depends(get_current_player),
):
    """Update shop (only owner)"""
    try:
        shop = await get_shop(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        await shop.fetch_related("owner_id")
        if shop.owner_id.id != player.id:
            raise HTTPException(status_code=403, detail="Only owner can update shop")

        updated = await update_shop(shop=shop, name=shop_data.name)
        await updated.fetch_related("owner_id")
        return ShopResponse(
            id=updated.id, owner_id=updated.owner_id.id, name=updated.name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update shop via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/shops/{shop_id}", response_model=SuccessResponse)
async def delete_shop_endpoint(
    shop_id: int, player: Player = Depends(get_current_player)
):
    """Delete shop (only owner)"""
    try:
        shop = await get_shop(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        await shop.fetch_related("owner_id")
        if shop.owner_id.id != player.id:
            raise HTTPException(status_code=403, detail="Only owner can delete shop")

        await delete_shop(shop)
        return SuccessResponse(message="Shop deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete shop via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shops/{shop_id}/items", response_model=ShopItemResponse, status_code=201)
async def create_shop_item_endpoint(
    shop_id: int,
    item_data: ShopItemCreate,
    player: Player = Depends(get_current_player),
):
    """Create shop item (only owner)"""
    try:
        shop = await get_shop(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        await shop.fetch_related("owner_id")
        if shop.owner_id.id != player.id:
            raise HTTPException(status_code=403, detail="Only owner can add items")

        item = await create_shop_item(
            shop=shop,
            item_id=item_data.item_id,
            price=item_data.price,
            quantity=item_data.quantity,
            total_count=item_data.total_count,
            item_nbt=item_data.item_nbt or "",
        )
        return ShopItemResponse.model_validate(item)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create shop item via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shops/{shop_id}/items", response_model=List[ShopItemResponse])
async def get_shop_items_endpoint(
    shop_id: int, player: Player = Depends(get_current_player)
):
    """Get shop items"""
    try:
        shop = await get_shop(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")

        items = await get_shop_items(shop)
        return [ShopItemResponse.model_validate(i) for i in items]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get shop items via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/shops/{shop_id}/items/full-sync",
    response_model=ShopItemsFullSyncResponse,
    status_code=200,
)
async def full_sync_shop_items_endpoint(
    shop_id: int,
    payload: ShopItemsFullSyncRequest,
    player: Player = Depends(get_current_player),
):
    """Full replace/sync of shop items from external source of truth."""
    try:
        shop = await get_shop(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        await shop.fetch_related("owner_id")
        if shop.owner_id.id != player.id:
            raise HTTPException(status_code=403, detail="Only owner can sync items")

        result = await sync_shop_items_full(
            shop=shop,
            items=[i.model_dump() for i in payload.items],
        )
        return ShopItemsFullSyncResponse(
            created=result["created"],
            updated=result["updated"],
            deleted=result["deleted"],
            total=result["total"],
            items=[ShopItemResponse.model_validate(i) for i in result["items"]],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to full-sync shop items via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/shops/{shop_id}/items/{item_id}/buy",
    response_model=ShopPurchaseResponse,
    status_code=200,
)
async def buy_shop_item_endpoint(
    shop_id: int,
    item_id: int,
    buy_data: ShopItemBuy,
    player: Player = Depends(get_current_player),
):
    """Buy item from shop (checks balance, transfers money to owner, decreases quantity)"""
    try:
        shop_item = await get_shop_item(item_id)
        if not shop_item:
            raise HTTPException(status_code=404, detail="Shop item not found")
        await shop_item.fetch_related("shop")
        if shop_item.shop.id != shop_id:
            raise HTTPException(status_code=404, detail="Shop item not found")

        quantity = buy_data.quantity
        if quantity < 1:
            raise HTTPException(status_code=400, detail="Quantity must be at least 1")

        updated = await buy_shop_item(
            buyer=player, shop_item=shop_item, quantity=quantity
        )
        return ShopPurchaseResponse(
            shop_item_id=updated.id,
            item_id=updated.item_id,
            quantity=quantity,
            total_paid=updated.price * quantity,
            remaining_total_count=updated.total_count,
        )
    except ValueError as e:
        if "Insufficient balance" in str(e):
            raise HTTPException(status_code=402, detail=str(e))
        if "Insufficient quantity" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to buy shop item via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/shops/{shop_id}/items/{item_id}", response_model=ShopItemResponse)
async def update_shop_item_endpoint(
    shop_id: int,
    item_id: int,
    item_data: ShopItemUpdate,
    player: Player = Depends(get_current_player),
):
    """Update shop item (only owner)"""
    try:
        shop = await get_shop(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        await shop.fetch_related("owner_id")
        if shop.owner_id.id != player.id:
            raise HTTPException(status_code=403, detail="Only owner can update items")

        shop_item = await get_shop_item(item_id)
        if not shop_item or shop_item.shop_id != shop_id:
            raise HTTPException(status_code=404, detail="Shop item not found")

        try:
            updated = await update_shop_item(
                shop_item=shop_item,
                price=item_data.price,
                quantity=item_data.quantity,
                total_count=item_data.total_count,
                item_nbt=item_data.item_nbt,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return ShopItemResponse.model_validate(updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update shop item via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/shops/{shop_id}/items/{item_id}", response_model=SuccessResponse)
async def delete_shop_item_endpoint(
    shop_id: int, item_id: int, player: Player = Depends(get_current_player)
):
    """Delete shop item (only owner)"""
    try:
        shop = await get_shop(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        await shop.fetch_related("owner_id")
        if shop.owner_id.id != player.id:
            raise HTTPException(status_code=403, detail="Only owner can delete items")

        shop_item = await get_shop_item(item_id)
        if not shop_item or shop_item.shop_id != shop_id:
            raise HTTPException(status_code=404, detail="Shop item not found")

        await delete_shop_item(shop_item)
        return SuccessResponse(message="Shop item deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete shop item via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
