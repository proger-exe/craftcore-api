"""
Announcements manager for CRUD operations on Announcement model
"""

from typing import Optional, List, Union
from datetime import datetime
from tortoise.expressions import Q
from core.models.mailing.announcements import Announcement, TargetAudience
from core.models.players.players import Player, PlayerRoles
from core.shared.logger import logger
from core.shared.utils import to_id


async def create_announcement(
    title: str,
    content: str,
    target_audience: TargetAudience = TargetAudience.ALL,
    author: Optional[Player] = None,
    priority: int = 0,
    scheduled_at: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
) -> Announcement:
    """
    Create a new announcement

    Args:
        title: Announcement title (max 128 chars)
        content: Announcement content
        target_audience: Target audience (default: ALL)
        author: Author player (optional, None for system announcements)
        priority: Display priority (default: 0)
        scheduled_at: Scheduled publication time (optional)
        expires_at: Expiration time (optional)

    Returns:
        Announcement: Created announcement instance

    Raises:
        Exception: If creation fails
    """
    try:
        announcement = await Announcement.create(
            title=title,
            content=content,
            author=author,
            is_active=True,
            priority=priority,
            target_audience=target_audience,
            scheduled_at=scheduled_at,
            expires_at=expires_at,
        )
        logger.info(
            "📢 Announcement created",
            announcement_id=announcement.id,
            target_audience=target_audience.value,
        )
        return announcement
    except Exception as e:
        logger.error("Failed to create announcement", error=str(e))
        raise


async def get_announcement(
    announcement: Union[int, Announcement],
) -> Optional[Announcement]:
    """
    Get announcement by ID или по экземпляру Announcement.

    Args:
        announcement: id объявления (int) или экземпляр Announcement

    Returns:
        Announcement or None if not found
    """
    try:
        aid = to_id(announcement)
        return await Announcement.get_or_none(id=aid)
    except Exception as e:
        logger.error(
            "Failed to get announcement",
            error=str(e),
            announcement_id=to_id(announcement),
        )
        raise


async def get_active_announcements(
    target_audience: Optional[TargetAudience] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Announcement]:
    """
    Get active announcements

    Args:
        target_audience: Filter by target audience (optional)
        limit: Maximum number of announcements to return
        offset: Number of announcements to skip

    Returns:
        List of Announcement instances
    """
    try:
        now = datetime.now()
        query = (
            Announcement.filter(is_active=True)
            .filter(Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=now))
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        )

        if target_audience is not None:
            query = query.filter(target_audience=target_audience)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-priority", "-created_at")
    except Exception as e:
        logger.error("Failed to get active announcements", error=str(e))
        raise


async def get_announcements_for_player(
    player: Player,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Announcement]:
    """
    Get announcements for specific player based on their role

    Args:
        player: Player instance
        limit: Maximum number of announcements to return
        offset: Number of announcements to skip

    Returns:
        List of Announcement instances
    """
    try:
        now = datetime.now()
        query = (
            Announcement.filter(is_active=True)
            .filter(Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=now))
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        )

        # Filter by player role
        if player.role == PlayerRoles.ADMIN or player.role == PlayerRoles.OWNER:
            query = query.filter(
                (Announcement.target_audience == TargetAudience.ALL)
                | (Announcement.target_audience == TargetAudience.ADMINS)
            )
        elif player.role == PlayerRoles.PLAYER:
            query = query.filter(
                (Announcement.target_audience == TargetAudience.ALL)
                | (Announcement.target_audience == TargetAudience.PLAYERS)
            )
        else:  # GUEST
            query = query.filter(
                (Announcement.target_audience == TargetAudience.ALL)
                | (Announcement.target_audience == TargetAudience.GUESTS)
            )

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-priority", "-created_at")
    except Exception as e:
        logger.error(
            "Failed to get announcements for player", error=str(e), player_id=player.id
        )
        raise


async def update_announcement(
    announcement: Announcement,
    title: Optional[str] = None,
    content: Optional[str] = None,
    target_audience: Optional[TargetAudience] = None,
    priority: Optional[int] = None,
    scheduled_at: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
) -> Announcement:
    """
    Update announcement fields

    Args:
        announcement: Announcement instance to update
        title: New title (optional)
        content: New content (optional)
        target_audience: New target audience (optional)
        priority: New priority (optional)
        scheduled_at: New scheduled time (optional)
        expires_at: New expiration time (optional)

    Returns:
        Updated Announcement instance

    Raises:
        Exception: If update fails
    """
    try:
        if title is not None:
            announcement.title = title
        if content is not None:
            announcement.content = content
        if target_audience is not None:
            announcement.target_audience = target_audience
        if priority is not None:
            announcement.priority = priority
        if scheduled_at is not None:
            announcement.scheduled_at = scheduled_at
        if expires_at is not None:
            announcement.expires_at = expires_at

        await announcement.save()
        logger.info("🔄 Announcement updated", announcement_id=announcement.id)
        return announcement
    except Exception as e:
        logger.error(
            "Failed to update announcement",
            error=str(e),
            announcement_id=announcement.id,
        )
        raise


async def deactivate_announcement(announcement: Announcement) -> Announcement:
    """
    Deactivate announcement

    Args:
        announcement: Announcement instance to deactivate

    Returns:
        Updated Announcement instance

    Raises:
        Exception: If update fails
    """
    try:
        announcement.is_active = False
        await announcement.save()
        logger.info("❌ Announcement deactivated", announcement_id=announcement.id)
        return announcement
    except Exception as e:
        logger.error(
            "Failed to deactivate announcement",
            error=str(e),
            announcement_id=announcement.id,
        )
        raise


async def delete_announcement(announcement: Announcement) -> None:
    """
    Delete announcement

    Args:
        announcement: Announcement instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        announcement_id = announcement.id
        await announcement.delete()
        logger.info("🗑️ Announcement deleted", announcement_id=announcement_id)
    except Exception as e:
        logger.error(
            "Failed to delete announcement",
            error=str(e),
            announcement_id=announcement_id,
        )
        raise
