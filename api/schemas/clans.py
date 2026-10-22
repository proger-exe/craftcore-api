"""
Clans schemas
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.models.social.clans import ClanRole


class ClanInventoryItem(BaseModel):
    """One clan inventory slot. Same item_id with different item_nbt = different slots."""

    item_id: str
    quantity: int = 0
    item_nbt: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "minecraft:diamond_sword",
                "quantity": 1,
                "item_nbt": "",
            }
        }


class ClanCreate(BaseModel):
    """Schema for creating a clan"""

    name: str
    tag: str
    description: str = ""
    prefix: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Elite Warriors",
                "tag": "EW",
                "description": "The best clan on the server",
                "prefix": "[EW]",
            }
        }


class ClanResponse(BaseModel):
    """Schema for clan response. members — массив [id, role] как ожидает плагин (BEGIN_ARRAY)."""

    id: int
    owner_id: int
    members: List[List[Union[int, str]]]  # [[player_id, role], ...]
    name: str
    description: str
    tag: str
    prefix: str
    inventory: List[ClanInventoryItem]
    balance: int
    homes: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClanUpdate(BaseModel):
    """Schema for updating a clan (все поля опциональны, передавать только то, что меняем).
    Поле inventory в теле не допускается — обновление инвентаря отключено (422 при передаче).
    """

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    description: Optional[str] = None
    tag: Optional[str] = None
    prefix: Optional[str] = None
    homes: Optional[List[Dict[str, Any]]] = None


class ClanMemberAdd(BaseModel):
    """Schema for adding a clan member"""

    player_id: int
    role: ClanRole = ClanRole.MEMBER


class ClanMemberUpdate(BaseModel):
    """Schema for updating a clan member role"""

    role: ClanRole
