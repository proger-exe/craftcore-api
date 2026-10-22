"""
User mailing router for announcements and notifications
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from api.schemas.mailing import (
    AnnouncementResponse,
    NotificationResponse,
)
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player, validate_pagination
from core.models.players.players import Player
from core.models.mailing.notifications import NotificationType
from core.managers.mailing.announcements import (
    get_announcement,
    get_announcements_for_player,
)
from core.managers.mailing.notifications import (
    get_player_notifications,
    get_unread_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
    delete_notification,
)
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "mailing"])


# Announcement endpoints


@router.get("/announcements", response_model=List[AnnouncementResponse])
async def get_announcements_endpoint(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get active announcements for player"""
    try:
        pagination = validate_pagination(page=page, per_page=per_page)
        announcements = await get_announcements_for_player(
            player=player,
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )
        return [AnnouncementResponse.model_validate(a) for a in announcements]
    except Exception as e:
        logger.error("Failed to get announcements via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement_endpoint(
    announcement_id: int, player: Player = Depends(get_current_player)
):
    """Get announcement by ID"""
    announcement = await get_announcement(announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return AnnouncementResponse.model_validate(announcement)


# Notification endpoints


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications_endpoint(
    is_read: bool = Query(None),
    notification_type: Optional[NotificationType] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get player notifications"""
    try:
        pagination = validate_pagination(page=page, per_page=per_page)
        notifications = await get_player_notifications(
            player=player,
            is_read=is_read,
            notification_type=notification_type,
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )
        return [NotificationResponse.model_validate(n) for n in notifications]
    except Exception as e:
        logger.error("Failed to get notifications via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/unread", response_model=List[NotificationResponse])
async def get_unread_notifications_endpoint(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get unread notifications"""
    try:
        pagination = validate_pagination(page=page, per_page=per_page)
        notifications = await get_unread_notifications(
            player=player,
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )
        return [NotificationResponse.model_validate(n) for n in notifications]
    except Exception as e:
        logger.error("Failed to get unread notifications via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/unread-count", response_model=dict)
async def get_unread_count_endpoint(
    player: Player = Depends(get_current_player),
):
    """Get count of unread notifications"""
    try:
        count = await get_unread_count(player)
        return {"unread_count": count}
    except Exception as e:
        logger.error("Failed to get unread count via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/notifications/{notification_id}/read", response_model=NotificationResponse
)
async def mark_notification_read_endpoint(
    notification_id: int, player: Player = Depends(get_current_player)
):
    """Mark notification as read"""
    try:
        from core.managers.mailing.notifications import get_notification

        notification = await get_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.player and notification.player.id != player.id:
            raise HTTPException(status_code=403, detail="Access denied")

        marked = await mark_as_read(notification)
        return NotificationResponse.model_validate(marked)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark notification as read via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/read-all", response_model=SuccessResponse)
async def mark_all_notifications_read_endpoint(
    player: Player = Depends(get_current_player),
):
    """Mark all notifications as read"""
    try:
        count = await mark_all_as_read(player)
        return SuccessResponse(message=f"Marked {count} notifications as read")
    except Exception as e:
        logger.error("Failed to mark all notifications as read via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notifications/{notification_id}", response_model=SuccessResponse)
async def delete_notification_endpoint(
    notification_id: int, player: Player = Depends(get_current_player)
):
    """Delete notification"""
    try:
        from core.managers.mailing.notifications import get_notification

        notification = await get_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.player and notification.player.id != player.id:
            raise HTTPException(status_code=403, detail="Access denied")

        await delete_notification(notification)
        return SuccessResponse(message="Notification deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete notification via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
