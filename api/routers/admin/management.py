"""
Admin management router for statistics and announcements
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from api.schemas.mailing import (
    AnnouncementCreate,
    AnnouncementResponse,
    AnnouncementUpdate,
    NotificationBulkCreate,
)
from api.schemas.common import SuccessResponse
from api.schemas.admin import PlayerSearchResult
from api.dependencies import get_current_admin, get_current_support
from core.models.players.players import Player, PlayerRoles
from core.managers.players.players import get_player, search_players
from core.managers.mailing.announcements import (
    create_announcement,
    get_announcement,
    update_announcement,
    delete_announcement,
)
from core.managers.mailing.notifications import (
    create_bulk_notification,
    send_notification_to_role,
)
from core.shared.analytics import (
    get_player_statistics,
    get_server_statistics,
    get_economy_statistics,
)
from core.shared.logger import logger

router = APIRouter(prefix="/admin", tags=["admin", "management"])


# Dashboard: player search


@router.get("/players/search", response_model=list[PlayerSearchResult])
async def search_players_endpoint(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    admin: Player = Depends(get_current_support),
):
    """Search players by nickname, tg_id, or ds_id. For Admin/Moderator/Support."""
    try:
        players = await search_players(query=query, limit=limit)
        return [
            PlayerSearchResult(
                player_id=p.id,
                tg_id=p.tg_id,
                nickname=p.nickname,
                role=p.role.value,
            )
            for p in players
        ]
    except Exception as e:
        logger.error("Failed to search players via API", error=str(e), query=query)
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoints


@router.get("/statistics/player/{player_id}")
async def get_player_statistics_endpoint(
    player_id: int, admin: Player = Depends(get_current_admin)
):
    """Get comprehensive statistics for a player"""
    try:
        player = await get_player(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        stats = await get_player_statistics(player)
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get player statistics via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/player/{player_id}/dossier")
async def get_player_dossier_endpoint(
    player_id: int, admin: Player = Depends(get_current_support)
):
    """Get full player dossier (profile, analytics, transactions, quests, clan, friends)."""
    try:
        player = await get_player(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        dossier = await get_player_statistics(player)
        return dossier
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get player dossier via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/server")
async def get_server_statistics_endpoint(admin: Player = Depends(get_current_admin)):
    """Get server-wide statistics"""
    try:
        stats = await get_server_statistics()
        return stats
    except Exception as e:
        logger.error("Failed to get server statistics via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/economy")
async def get_economy_statistics_endpoint(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    admin: Player = Depends(get_current_admin),
):
    """Get economy statistics for a date range"""
    try:
        stats = await get_economy_statistics(start_date=start_date, end_date=end_date)
        return stats
    except Exception as e:
        logger.error("Failed to get economy statistics via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Announcements management endpoints


@router.post("/announcements", response_model=AnnouncementResponse, status_code=201)
async def create_announcement_endpoint(
    announcement_data: AnnouncementCreate,
    admin: Player = Depends(get_current_admin),
):
    """Create a new announcement"""
    try:
        announcement = await create_announcement(
            title=announcement_data.title,
            content=announcement_data.content,
            target_audience=announcement_data.target_audience,
            author=admin,
            priority=announcement_data.priority,
            scheduled_at=announcement_data.scheduled_at,
            expires_at=announcement_data.expires_at,
        )
        return AnnouncementResponse.model_validate(announcement)
    except Exception as e:
        logger.error("Failed to create announcement via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement_endpoint(
    announcement_id: int,
    announcement_data: AnnouncementUpdate,
    admin: Player = Depends(get_current_admin),
):
    """Update an announcement"""
    try:
        announcement = await get_announcement(announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")

        updated = await update_announcement(
            announcement=announcement,
            title=announcement_data.title,
            content=announcement_data.content,
            target_audience=announcement_data.target_audience,
            priority=announcement_data.priority,
            scheduled_at=announcement_data.scheduled_at,
            expires_at=announcement_data.expires_at,
        )
        return AnnouncementResponse.model_validate(updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update announcement via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/announcements/{announcement_id}", response_model=SuccessResponse)
async def delete_announcement_endpoint(
    announcement_id: int, admin: Player = Depends(get_current_admin)
):
    """Delete an announcement"""
    try:
        announcement = await get_announcement(announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")

        await delete_announcement(announcement)
        return SuccessResponse(message="Announcement deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete announcement via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Notifications management endpoints


@router.post("/notifications/bulk", response_model=SuccessResponse)
async def create_bulk_notification_endpoint(
    notification_data: NotificationBulkCreate,
    admin: Player = Depends(get_current_admin),
):
    """Send bulk notifications"""
    try:
        players = None
        if notification_data.player_ids:
            players = await Player.filter(id__in=notification_data.player_ids)

        notifications = await create_bulk_notification(
            title=notification_data.title,
            content=notification_data.content,
            notification_type=notification_data.notification_type,
            players=players,
        )

        return SuccessResponse(
            message=f"Sent {len(notifications)} notifications successfully"
        )
    except Exception as e:
        logger.error("Failed to send bulk notifications via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/role", response_model=SuccessResponse)
async def send_notification_to_role_endpoint(
    role: PlayerRoles,
    title: str,
    content: str,
    notification_type: str = "info",
    admin: Player = Depends(get_current_admin),
):
    """Send notification to all players with specific role"""
    try:
        from core.models.mailing.notifications import NotificationType

        notif_type = NotificationType(notification_type)
        count = await send_notification_to_role(
            role=role,
            title=title,
            content=content,
            notification_type=notif_type,
        )

        return SuccessResponse(
            message=f"Sent notifications to {count} players with role {role.value}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to send notification to role via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
