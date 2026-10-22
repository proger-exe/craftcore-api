"""
Notifications manager for CRUD operations on Notification model
"""

from typing import Optional, List, Union
from datetime import datetime
from core.models.mailing.notifications import Notification, NotificationType
from core.models.players.players import Player, PlayerRoles
from core.shared.logger import logger
from core.shared.utils import to_id


async def create_notification(
    title: str,
    content: str,
    notification_type: NotificationType = NotificationType.INFO,
    player: Optional[Player] = None,
) -> Notification:
    """
    Create a new notification

    Args:
        title: Notification title (max 128 chars)
        content: Notification content
        notification_type: Notification type (default: INFO)
        player: Recipient player (optional, None for bulk notifications)

    Returns:
        Notification: Created notification instance

    Raises:
        Exception: If creation fails
    """
    try:
        notification = await Notification.create(
            player=player,
            title=title,
            content=content,
            notification_type=notification_type,
            is_read=False,
        )
        logger.info(
            "🔔 Notification created",
            notification_id=notification.id,
            player_id=player.id if player else None,
            notification_type=notification_type.value,
        )
        return notification
    except Exception as e:
        logger.error("Failed to create notification", error=str(e))
        raise


async def create_bulk_notification(
    title: str,
    content: str,
    notification_type: NotificationType = NotificationType.INFO,
    players: Optional[List[Player]] = None,
) -> List[Notification]:
    """
    Create bulk notifications for multiple players

    Args:
        title: Notification title
        content: Notification content
        notification_type: Notification type (default: INFO)
        players: List of recipient players (optional, None for all players)

    Returns:
        List of created Notification instances

    Raises:
        Exception: If creation fails
    """
    try:
        if players:
            notifications = [
                Notification(
                    player=player,
                    title=title,
                    content=content,
                    notification_type=notification_type,
                    is_read=False,
                )
                for player in players
            ]
        else:
            # Create notification without player (bulk for all)
            notifications = [
                Notification(
                    player=None,
                    title=title,
                    content=content,
                    notification_type=notification_type,
                    is_read=False,
                )
            ]

        await Notification.bulk_create(notifications)

        logger.info(
            "📢 Bulk notification created",
            count=len(notifications),
            notification_type=notification_type.value,
        )
        return notifications
    except Exception as e:
        logger.error("Failed to create bulk notification", error=str(e))
        raise


async def get_notification(
    notification: Union[int, Notification],
) -> Optional[Notification]:
    """
    Get notification by ID или по экземпляру Notification.

    Args:
        notification: id уведомления (int) или экземпляр Notification

    Returns:
        Notification or None if not found
    """
    try:
        nid = to_id(notification)
        return await Notification.get_or_none(id=nid)
    except Exception as e:
        logger.error(
            "Failed to get notification",
            error=str(e),
            notification_id=to_id(notification),
        )
        raise


async def get_player_notifications(
    player: Player,
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Notification]:
    """
    Get notifications for player

    Args:
        player: Player instance
        is_read: Filter by read status (optional)
        notification_type: Filter by type (optional)
        limit: Maximum number of notifications to return
        offset: Number of notifications to skip

    Returns:
        List of Notification instances
    """
    try:
        query = Notification.filter(player=player)

        if is_read is not None:
            query = query.filter(is_read=is_read)
        if notification_type is not None:
            query = query.filter(notification_type=notification_type)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error(
            "Failed to get player notifications", error=str(e), player_id=player.id
        )
        raise


async def get_unread_notifications(
    player: Player,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Notification]:
    """
    Get unread notifications for player

    Args:
        player: Player instance
        limit: Maximum number of notifications to return
        offset: Number of notifications to skip

    Returns:
        List of unread Notification instances
    """
    try:
        query = Notification.filter(player=player, is_read=False)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error(
            "Failed to get unread notifications", error=str(e), player_id=player.id
        )
        raise


async def mark_as_read(notification: Notification) -> Notification:
    """
    Mark notification as read

    Args:
        notification: Notification instance

    Returns:
        Updated Notification instance

    Raises:
        Exception: If update fails
    """
    try:
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now()
            await notification.save()
            logger.info(
                "✅ Notification marked as read", notification_id=notification.id
            )
        return notification
    except Exception as e:
        logger.error(
            "Failed to mark notification as read",
            error=str(e),
            notification_id=notification.id,
        )
        raise


async def mark_all_as_read(player: Player) -> int:
    """
    Mark all notifications as read for player

    Args:
        player: Player instance

    Returns:
        Number of notifications marked as read

    Raises:
        Exception: If update fails
    """
    try:
        count = await Notification.filter(player=player, is_read=False).update(
            is_read=True, read_at=datetime.now()
        )
        logger.info(
            "✅ All notifications marked as read", player_id=player.id, count=count
        )
        return count
    except Exception as e:
        logger.error("Failed to mark all as read", error=str(e), player_id=player.id)
        raise


async def delete_notification(notification: Notification) -> None:
    """
    Delete notification

    Args:
        notification: Notification instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        notification_id = notification.id
        await notification.delete()
        logger.info("🗑️ Notification deleted", notification_id=notification_id)
    except Exception as e:
        logger.error(
            "Failed to delete notification",
            error=str(e),
            notification_id=notification_id,
        )
        raise


async def get_unread_count(player: Player) -> int:
    """
    Get count of unread notifications for player

    Args:
        player: Player instance

    Returns:
        Number of unread notifications
    """
    try:
        return await Notification.filter(player=player, is_read=False).count()
    except Exception as e:
        logger.error("Failed to get unread count", error=str(e), player_id=player.id)
        raise


async def send_notification_to_role(
    role: PlayerRoles,
    title: str,
    content: str,
    notification_type: NotificationType = NotificationType.INFO,
) -> int:
    """
    Send notification to all players with specific role

    Args:
        role: Player role to send to
        title: Notification title
        content: Notification content
        notification_type: Notification type (default: INFO)

    Returns:
        Number of notifications sent
    """
    try:
        from core.managers.players.players import get_players_by_role

        players = await get_players_by_role(role)
        notifications = await create_bulk_notification(
            title=title,
            content=content,
            notification_type=notification_type,
            players=players,
        )

        logger.info(
            "📢 Notification sent to role",
            role=role.value,
            count=len(notifications),
        )
        return len(notifications)
    except Exception as e:
        logger.error(
            "Failed to send notification to role", error=str(e), role=role.value
        )
        raise
