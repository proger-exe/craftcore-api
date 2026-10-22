"""
Safety schemas for bans, mutes, warns, arrests, and admin logs
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class BanCreate(BaseModel):
    """Schema for creating a ban"""

    player_id: int
    reason: str
    expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": 1,
                "reason": "Cheating",
                "expires_at": "2024-12-31T23:59:59",
            }
        }


class BanResponse(BaseModel):
    """Schema for ban response"""

    id: int
    player_id: int
    admin_id: Optional[int] = None
    reason: str
    banned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    unbanned_at: Optional[datetime] = None
    unbanned_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class MuteCreate(BaseModel):
    """Schema for creating a mute"""

    player_id: int
    reason: str
    expires_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": 1,
                "reason": "Spam",
                "expires_at": "2024-12-31T23:59:59",
            }
        }


class MuteResponse(BaseModel):
    """Schema for mute response"""

    id: int
    player_id: int
    admin_id: Optional[int] = None
    reason: str
    muted_at: datetime
    expires_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class WarnCreate(BaseModel):
    """Schema for creating a warn"""

    player_id: int
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": 1,
                "reason": "Inappropriate behavior",
            }
        }


class WarnResponse(BaseModel):
    """Schema for warn response"""

    id: int
    player_id: int
    admin_id: int
    reason: str
    warned_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ArrestCreate(BaseModel):
    """Schema for creating an arrest"""

    player_id: int
    reason: str
    expires_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "player_id": 1,
                "reason": "Violation of server rules",
                "expires_at": "2024-12-31T23:59:59",
            }
        }


class ArrestResponse(BaseModel):
    """Schema for arrest response"""

    id: int
    player_id: int
    admin_id: Optional[int] = None
    reason: str
    arrested_at: datetime
    expires_at: datetime
    is_active: bool
    released_at: Optional[datetime] = None
    released_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class AdminActionLogResponse(BaseModel):
    """Schema for admin action log response"""

    id: int
    admin_id: int
    action_type: str
    target_player_id: Optional[int] = None
    details: dict
    created_at: datetime

    class Config:
        from_attributes = True
