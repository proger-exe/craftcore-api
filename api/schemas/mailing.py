"""
Mailing schemas for announcements and notifications
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from core.models.mailing.announcements import TargetAudience
from core.models.mailing.notifications import NotificationType


class AnnouncementCreate(BaseModel):
    """Schema for creating an announcement"""

    title: str
    content: str
    target_audience: TargetAudience = TargetAudience.ALL
    priority: int = 0
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Server Maintenance",
                "content": "Server will be under maintenance tomorrow",
                "target_audience": "all",
                "priority": 10,
            }
        }


class AnnouncementResponse(BaseModel):
    """Schema for announcement response"""

    id: int
    title: str
    content: str
    author_id: Optional[int] = None
    is_active: bool
    priority: int
    target_audience: str
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementUpdate(BaseModel):
    """Schema for updating an announcement"""

    title: Optional[str] = None
    content: Optional[str] = None
    target_audience: Optional[TargetAudience] = None
    priority: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationCreate(BaseModel):
    """Schema for creating a notification"""

    title: str
    content: str
    notification_type: NotificationType = NotificationType.INFO
    player_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "New quest available",
                "content": "A new quest has been added to the game",
                "notification_type": "info",
            }
        }


class NotificationResponse(BaseModel):
    """Schema for notification response"""

    id: int
    player_id: Optional[int] = None
    title: str
    content: str
    notification_type: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationBulkCreate(BaseModel):
    """Schema for bulk notification creation"""

    title: str
    content: str
    notification_type: NotificationType = NotificationType.INFO
    player_ids: Optional[list[int]] = None  # None = all players
