"""
Shops schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ShopCreate(BaseModel):
    """Schema for creating a shop"""

    name: str = "Shop"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Shop",
            }
        }


class ShopResponse(BaseModel):
    """Schema for shop response"""

    id: int
    owner_id: int
    name: str

    class Config:
        from_attributes = True


class ShopUpdate(BaseModel):
    """Schema for updating a shop"""

    name: Optional[str] = None


class ShopItemCreate(BaseModel):
    """Schema for creating a shop item"""

    item_id: str
    price: int
    quantity: int = 1
    total_count: int = 0
    item_nbt: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "minecraft:diamond",
                "price": 100,
                "quantity": 1,
                "total_count": 10,
            }
        }


class ShopItemResponse(BaseModel):
    """Schema for shop item response"""

    id: int
    item_id: str
    shop_id: int
    price: int
    quantity: int
    total_count: int
    item_nbt: str = ""

    class Config:
        from_attributes = True


class ShopItemUpdate(BaseModel):
    """Schema for updating a shop item"""

    price: Optional[int] = None
    quantity: Optional[int] = None
    total_count: Optional[int] = None
    item_nbt: Optional[str] = None


class ShopItemBuy(BaseModel):
    """Schema for buying a shop item"""

    quantity: int = 1

    class Config:
        json_schema_extra = {"example": {"quantity": 1}}


class ShopItemsFullSyncRequest(BaseModel):
    """Schema for full items sync (source of truth from Minecraft)"""

    items: List[ShopItemCreate]


class ShopItemsFullSyncResponse(BaseModel):
    """Schema for full sync result"""

    created: int
    updated: int
    deleted: int
    total: int
    items: List[ShopItemResponse]


class ShopPurchaseResponse(BaseModel):
    """Schema for purchase result"""

    shop_item_id: int
    item_id: str
    quantity: int
    total_paid: int
    remaining_total_count: int


class ShopWithItemsResponse(ShopResponse):
    """Schema for shop with items"""

    items: List[ShopItemResponse] = []
