"""
Party schemas
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class PartyCreate(BaseModel):
    """Schema for creating a party"""

    name: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Adventure Squad",
            }
        }


class PartyResponse(BaseModel):
    """Schema for party response"""

    id: int
    name: str
    leader_id: int
    members: List[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PartyUpdate(BaseModel):
    """Schema for updating a party"""

    name: Optional[str] = None


class PartyMemberAdd(BaseModel):
    """Schema for adding a party member"""

    player_id: int
