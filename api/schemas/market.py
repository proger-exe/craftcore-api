"""
Market schemas
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class MarketItemCreate(BaseModel):
    """Schema for creating a market item"""

    item_id: str
    name: str
    desc: str
    total_price: int
    quantity: int

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "minecraft:diamond",
                "name": "Diamond",
                "desc": "High quality diamond",
                "total_price": 1000,
                "quantity": 5,
            }
        }


class MarketItemResponse(BaseModel):
    """Schema for market item response"""

    id: int
    item_id: str
    seller_id: int
    name: str
    desc: str
    total_price: int
    quantity: int

    class Config:
        from_attributes = True


class MarketItemUpdate(BaseModel):
    """Schema for updating a market item"""

    name: Optional[str] = None
    desc: Optional[str] = None
    total_price: Optional[int] = None
    quantity: Optional[int] = None
