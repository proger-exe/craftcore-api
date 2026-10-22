"""
User market router
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from api.schemas.market import MarketItemCreate, MarketItemResponse, MarketItemUpdate
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player, validate_pagination
from core.models.players.players import Player
from core.managers.economics.market import (
    create_market_item,
    get_market_item,
    get_market_items,
    get_market_items_by_seller,
    # search_market_items,
    update_market_item,
    delete_market_item,
)
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "market"])


@router.post("/market/items", response_model=MarketItemResponse, status_code=201)
async def create_market_item_endpoint(
    item_data: MarketItemCreate, player: Player = Depends(get_current_player)
):
    """Create a new market item"""
    try:
        item = await create_market_item(
            seller=player,
            item_id=item_data.item_id,
            name=item_data.name,
            desc=item_data.desc,
            total_price=item_data.total_price,
            quantity=item_data.quantity,
        )
        return MarketItemResponse.model_validate(item)
    except Exception as e:
        logger.error("Failed to create market item via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/items", response_model=List[MarketItemResponse])
async def get_market_items_endpoint(
    seller_id: Optional[int] = Query(None),
    item_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get market items with optional filters"""
    try:
        pagination = validate_pagination(page=page, per_page=per_page)

        # if search:
        #    # items = await search_market_items(query=search)
        if seller_id:
            from core.managers.players.players import get_player

            seller = await get_player(seller_id)
            if not seller:
                raise HTTPException(status_code=404, detail="Seller not found")
            items = await get_market_items_by_seller(seller)
        else:
            items = await get_market_items(
                item_id=item_id,
                limit=pagination["per_page"],
                offset=(pagination["page"] - 1) * pagination["per_page"],
            )

        return [MarketItemResponse.model_validate(i) for i in items]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get market items via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/items/{item_id}", response_model=MarketItemResponse)
async def get_market_item_endpoint(
    item_id: int, player: Player = Depends(get_current_player)
):
    """Get market item by ID"""
    item = await get_market_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Market item not found")
    return MarketItemResponse.model_validate(item)


@router.put("/market/items/{item_id}", response_model=MarketItemResponse)
async def update_market_item_endpoint(
    item_id: int,
    item_data: MarketItemUpdate,
    player: Player = Depends(get_current_player),
):
    """Update market item (only seller)"""
    try:
        item = await get_market_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Market item not found")

        if item.seller_id != player.id:
            raise HTTPException(status_code=403, detail="Only seller can update item")

        updated = await update_market_item(
            market_item=item,
            name=item_data.name,
            desc=item_data.desc,
            total_price=item_data.total_price,
            quantity=item_data.quantity,
        )
        return MarketItemResponse.model_validate(updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update market item via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/market/items/{item_id}", response_model=SuccessResponse)
async def delete_market_item_endpoint(
    item_id: int, player: Player = Depends(get_current_player)
):
    """Delete market item (only seller)"""
    try:
        item = await get_market_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Market item not found")

        if item.seller_id != player.id:
            raise HTTPException(status_code=403, detail="Only seller can delete item")

        await delete_market_item(item)
        return SuccessResponse(message="Market item deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete market item via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
