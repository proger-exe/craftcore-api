"""
Social schemas for friends
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from core.models.social.friends import FriendStatus


class FriendRequest(BaseModel):
    """Schema for friend request (friend_id or friendId)"""

    friend_id: int = Field(
        ..., alias="friendId", description="ID of player to add as friend"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "friend_id": 2,
            }
        }


class FriendResponse(BaseModel):
    """Schema for friend response"""

    id: int
    player_id: int
    friend_id: int
    status: str
    requested_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FriendStatusUpdate(BaseModel):
    """Schema for updating friend status"""

    status: FriendStatus


class MutualFriendsResponse(BaseModel):
    """Schema for mutual friends response"""

    player1_id: int
    player2_id: int
    mutual_friends: List[dict]
    count: int
