"""
Friends manager for CRUD operations on Friend model
"""

from typing import Optional, List
from datetime import datetime
from core.models.social.friends import Friend, FriendStatus
from core.models.players.players import Player
from core.shared.logger import logger


async def send_friend_request(player: Player, friend: Player) -> Friend:
    """
    Send friend request

    Args:
        player: Player who sends request
        friend: Player to add as friend

    Returns:
        Friend: Created friend relationship instance

    Raises:
        ValueError: If trying to add self as friend or relationship already exists
        Exception: If creation fails
    """
    if player.id == friend.id:
        raise ValueError("Cannot add yourself as friend")

    existing = await Friend.get_or_none(player=player, friend=friend)
    if existing:
        raise ValueError("Friend relationship already exists")

    # Check reverse relationship
    reverse = await Friend.get_or_none(player=friend, friend=player)
    if reverse:
        raise ValueError("Friend relationship already exists (reverse)")

    try:
        friend_rel = await Friend.create(
            player=player,
            friend=friend,
            status=FriendStatus.PENDING,
        )
        logger.info(
            "👥 Friend request sent",
            friend_id=friend_rel.id,
            player_id=player.id,
            friend_player_id=friend.id,
        )
        return friend_rel
    except Exception as e:
        logger.error(
            "Failed to send friend request",
            error=str(e),
            player_id=player.id,
            friend_id=friend.id,
        )
        raise


async def accept_friend_request(friend_rel: Friend) -> Friend:
    """
    Accept friend request

    Args:
        friend_rel: Friend relationship instance

    Returns:
        Updated Friend instance

    Raises:
        ValueError: If request is not pending
        Exception: If update fails
    """
    if friend_rel.status != FriendStatus.PENDING:
        raise ValueError("Friend request is not pending")

    try:
        friend_rel.status = FriendStatus.ACCEPTED
        friend_rel.accepted_at = datetime.now()
        await friend_rel.save()

        # Create reverse relationship if it doesn't exist
        reverse = await Friend.get_or_none(
            player=friend_rel.friend, friend=friend_rel.player
        )
        if not reverse:
            await Friend.create(
                player=friend_rel.friend,
                friend=friend_rel.player,
                status=FriendStatus.ACCEPTED,
                accepted_at=datetime.now(),
            )

        logger.info(
            "✅ Friend request accepted",
            friend_id=friend_rel.id,
            player_id=friend_rel.player.id,
            friend_player_id=friend_rel.friend.id,
        )
        return friend_rel
    except Exception as e:
        logger.error(
            "Failed to accept friend request", error=str(e), friend_id=friend_rel.id
        )
        raise


async def reject_friend_request(friend_rel: Friend) -> None:
    """
    Reject friend request (delete relationship)

    Args:
        friend_rel: Friend relationship instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        friend_id = friend_rel.id
        await friend_rel.delete()
        logger.info("❌ Friend request rejected", friend_id=friend_id)
    except Exception as e:
        logger.error(
            "Failed to reject friend request", error=str(e), friend_id=friend_id
        )
        raise


async def remove_friend(player: Player, friend: Player) -> None:
    """
    Remove friend (delete relationship from both sides)

    Args:
        player: Player instance
        friend: Friend player instance

    Raises:
        Exception: If deletion fails
    """
    try:
        # Delete both relationships
        rel1 = await Friend.get_or_none(player=player, friend=friend)
        rel2 = await Friend.get_or_none(player=friend, friend=player)

        if rel1:
            await rel1.delete()
        if rel2:
            await rel2.delete()

        logger.info(
            "🗑️ Friend removed",
            player_id=player.id,
            friend_id=friend.id,
        )
    except Exception as e:
        logger.error(
            "Failed to remove friend",
            error=str(e),
            player_id=player.id,
            friend_id=friend.id,
        )
        raise


async def block_friend(player: Player, friend: Player) -> Friend:
    """
    Block friend

    Args:
        player: Player instance
        friend: Friend player instance

    Returns:
        Updated or created Friend instance

    Raises:
        Exception: If update fails
    """
    try:
        friend_rel = await Friend.get_or_none(player=player, friend=friend)
        if not friend_rel:
            friend_rel = await Friend.create(
                player=player,
                friend=friend,
                status=FriendStatus.BLOCKED,
            )
        else:
            friend_rel.status = FriendStatus.BLOCKED
            await friend_rel.save()

        logger.info(
            "🚫 Friend blocked",
            friend_id=friend_rel.id,
            player_id=player.id,
            friend_player_id=friend.id,
        )
        return friend_rel
    except Exception as e:
        logger.error(
            "Failed to block friend",
            error=str(e),
            player_id=player.id,
            friend_id=friend.id,
        )
        raise


async def unblock_friend(player: Player, friend: Player) -> Optional[Friend]:
    """
    Unblock friend

    Args:
        player: Player instance
        friend: Friend player instance

    Returns:
        Updated Friend instance or None if not found

    Raises:
        Exception: If update fails
    """
    try:
        friend_rel = await Friend.get_or_none(player=player, friend=friend)
        if friend_rel and friend_rel.status == FriendStatus.BLOCKED:
            friend_rel.status = FriendStatus.PENDING
            await friend_rel.save()
            logger.info(
                "🔓 Friend unblocked",
                friend_id=friend_rel.id,
                player_id=player.id,
                friend_player_id=friend.id,
            )
            return friend_rel
        return None
    except Exception as e:
        logger.error(
            "Failed to unblock friend",
            error=str(e),
            player_id=player.id,
            friend_id=friend.id,
        )
        raise


async def get_player_friends(
    player: Player, status: FriendStatus = FriendStatus.ACCEPTED
) -> List[Friend]:
    """
    Get all friends for player

    Args:
        player: Player instance
        status: Friend status filter (default: ACCEPTED)

    Returns:
        List of Friend instances
    """
    try:
        return await Friend.filter(player=player, status=status).all()
    except Exception as e:
        logger.error("Failed to get player friends", error=str(e), player_id=player.id)
        raise


async def get_friend_requests(player: Player, incoming: bool = True) -> List[Friend]:
    """
    Get friend requests for player

    Args:
        player: Player instance
        incoming: If True, get incoming requests, else outgoing requests

    Returns:
        List of Friend instances
    """
    try:
        if incoming:
            return await Friend.filter(friend=player, status=FriendStatus.PENDING).all()
        else:
            return await Friend.filter(player=player, status=FriendStatus.PENDING).all()
    except Exception as e:
        logger.error("Failed to get friend requests", error=str(e), player_id=player.id)
        raise


async def are_friends(player1: Player, player2: Player) -> bool:
    """
    Check if two players are friends

    Args:
        player1: First player
        player2: Second player

    Returns:
        True if players are friends, False otherwise
    """
    try:
        friend_rel = await Friend.get_or_none(
            player=player1, friend=player2, status=FriendStatus.ACCEPTED
        )
        return friend_rel is not None
    except Exception as e:
        logger.error(
            "Failed to check if friends",
            error=str(e),
            player1_id=player1.id,
            player2_id=player2.id,
        )
        raise


async def is_blocked(player: Player, friend: Player) -> bool:
    """
    Check if player blocked friend

    Args:
        player: Player instance
        friend: Friend player instance

    Returns:
        True if blocked, False otherwise
    """
    try:
        friend_rel = await Friend.get_or_none(
            player=player, friend=friend, status=FriendStatus.BLOCKED
        )
        return friend_rel is not None
    except Exception as e:
        logger.error(
            "Failed to check if blocked",
            error=str(e),
            player_id=player.id,
            friend_id=friend.id,
        )
        raise


async def get_friend_relationship(player: Player, friend: Player) -> Optional[Friend]:
    """
    Get friend relationship between two players

    Args:
        player: First player
        friend: Second player

    Returns:
        Friend relationship or None if not found
    """
    try:
        return await Friend.get_or_none(player=player, friend=friend)
    except Exception as e:
        logger.error(
            "Failed to get friend relationship",
            error=str(e),
            player_id=player.id,
            friend_id=friend.id,
        )
        raise


async def get_mutual_friends(player1: Player, player2: Player) -> List[Player]:
    """
    Get mutual friends between two players

    Args:
        player1: First player
        player2: Second player

    Returns:
        List of mutual Player instances
    """
    try:
        friends1 = await get_player_friends(player1, status=FriendStatus.ACCEPTED)
        friends2 = await get_player_friends(player2, status=FriendStatus.ACCEPTED)

        friends1_ids = {f.friend.id for f in friends1}
        friends2_ids = {f.friend.id for f in friends2}

        mutual_ids = friends1_ids & friends2_ids

        mutual_friends = []
        for friend_id in mutual_ids:
            player = await Player.get_or_none(id=friend_id)
            if player:
                mutual_friends.append(player)

        return mutual_friends
    except Exception as e:
        logger.error(
            "Failed to get mutual friends",
            error=str(e),
            player1_id=player1.id,
            player2_id=player2.id,
        )
        raise


async def get_friend_suggestions(player: Player, limit: int = 10) -> List[Player]:
    """
    Get friend suggestions based on mutual friends

    Args:
        player: Player instance
        limit: Maximum number of suggestions (default: 10)

    Returns:
        List of suggested Player instances
    """
    try:
        # Get player's friends
        player_friends = await get_player_friends(player, status=FriendStatus.ACCEPTED)
        player_friend_ids = {f.friend.id for f in player_friends}
        player_friend_ids.add(player.id)  # Exclude self

        # Get friends of friends
        suggestions_count = {}
        for friend_rel in player_friends:
            friend = friend_rel.friend
            friend_friends = await get_player_friends(
                friend, status=FriendStatus.ACCEPTED
            )

            for friend_friend_rel in friend_friends:
                suggested_id = friend_friend_rel.friend.id

                # Skip if already friend or self
                if suggested_id in player_friend_ids:
                    continue

                # Count mutual friends
                if suggested_id not in suggestions_count:
                    suggestions_count[suggested_id] = 0
                suggestions_count[suggested_id] += 1

        # Sort by mutual friends count and get top
        sorted_suggestions = sorted(
            suggestions_count.items(), key=lambda x: x[1], reverse=True
        )[:limit]

        # Get player objects
        suggestions = []
        for suggested_id, _ in sorted_suggestions:
            suggested_player = await Player.get_or_none(id=suggested_id)
            if suggested_player:
                suggestions.append(suggested_player)

        return suggestions
    except Exception as e:
        logger.error(
            "Failed to get friend suggestions", error=str(e), player_id=player.id
        )
        raise
