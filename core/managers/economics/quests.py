"""
Quests manager for CRUD operations on Quest and QuestProgress models
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from tortoise.expressions import Q
from tortoise.transactions import in_transaction
from core.models.economics.quests import Quest, QuestProgress, QuestType, QuestStatus
from core.models.players.players import Player
from core.shared.logger import logger
from core.shared.utils import to_id
from core.managers.economics.utils import validate_amount


# Quest CRUD operations


async def create_quest(
    title: str,
    description: str,
    quest_type: QuestType,
    reward_amount: int = 0,
    payment_amount: int = 0,
    creator: Optional[Player] = None,
    max_completions: Optional[int] = None,
    expires_at: Optional[datetime] = None,
    requirements: Optional[Dict] = None,
) -> Quest:
    """
    Create a new quest

    Args:
        title: Quest title (max 128 chars)
        description: Quest description
        quest_type: Quest type (SYSTEM or PLAYER)
        reward_amount: Reward in money (default: 0)
        payment_amount: Payment for completion (default: 0, for player quests)
        creator: Creator player (optional, None for system quests)
        max_completions: Maximum number of completions (optional, None = unlimited)
        expires_at: Expiration time (optional)
        requirements: Quest requirements (optional, JSON dict)

    Returns:
        Quest: Created quest instance

    Raises:
        ValueError: If reward_amount or payment_amount is negative
        Exception: If creation fails
    """
    reward_amount = validate_amount(amount=reward_amount)
    payment_amount = validate_amount(amount=payment_amount)

    if quest_type == QuestType.PLAYER and creator is None:
        raise ValueError("Player quests must have a creator")

    try:
        quest = await Quest.create(
            creator=creator,
            title=title,
            description=description,
            quest_type=quest_type,
            reward_amount=reward_amount,
            payment_amount=payment_amount,
            status=QuestStatus.ACTIVE,
            max_completions=max_completions,
            current_completions=0,
            expires_at=expires_at,
            requirements=requirements or {},
        )
        logger.info(
            "📜 Quest created",
            quest_id=quest.id,
            quest_type=quest_type.value,
            creator_id=creator.id if creator else None,
        )
        return quest
    except Exception as e:
        logger.error(
            "Failed to create quest", error=str(e), quest_type=quest_type.value
        )
        raise


async def get_quest(quest: Union[int, Quest]) -> Optional[Quest]:
    """
    Get quest by ID или по экземпляру Quest.

    Args:
        quest: id квеста (int) или экземпляр Quest

    Returns:
        Quest or None if not found
    """
    try:
        qid = to_id(quest)
        return await Quest.get_or_none(id=qid)
    except Exception as e:
        logger.error("Failed to get quest", error=str(e), quest_id=to_id(quest))
        raise


async def get_active_quests(
    quest_type: Optional[QuestType] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Quest]:
    """
    Get active quests

    Args:
        quest_type: Filter by quest type (optional)
        limit: Maximum number of quests to return
        offset: Number of quests to skip

    Returns:
        List of Quest instances
    """
    try:
        now = datetime.now()
        query = Quest.filter(
            status=QuestStatus.ACTIVE,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))

        if quest_type is not None:
            query = query.filter(quest_type=quest_type)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error("Failed to get active quests", error=str(e))
        raise


async def get_player_quests(
    player: Player,
    quest_type: Optional[QuestType] = None,
    status: Optional[QuestStatus] = None,
) -> List[Quest]:
    """
    Get quests created by player

    Args:
        player: Player instance
        quest_type: Filter by quest type (optional)
        status: Filter by status (optional)

    Returns:
        List of Quest instances
    """
    try:
        query = Quest.filter(creator=player)

        if quest_type is not None:
            query = query.filter(quest_type=quest_type)
        if status is not None:
            query = query.filter(status=status)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error("Failed to get player quests", error=str(e), player_id=player.id)
        raise


async def update_quest(
    quest: Quest,
    title: Optional[str] = None,
    description: Optional[str] = None,
    reward_amount: Optional[int] = None,
    payment_amount: Optional[int] = None,
    max_completions: Optional[int] = None,
    expires_at: Optional[datetime] = None,
    requirements: Optional[Dict] = None,
) -> Quest:
    """
    Update quest fields

    Args:
        quest: Quest instance to update
        title: New title (optional)
        description: New description (optional)
        reward_amount: New reward amount (optional)
        payment_amount: New payment amount (optional)
        max_completions: New max completions (optional)
        expires_at: New expiration time (optional)
        requirements: New requirements (optional)

    Returns:
        Updated Quest instance

    Raises:
        ValueError: If reward_amount or payment_amount is negative
        Exception: If update fails
    """
    try:
        if title is not None:
            quest.title = title
        if description is not None:
            quest.description = description
        if reward_amount is not None:
            reward_amount = validate_amount(amount=reward_amount)
            quest.reward_amount = reward_amount
        if payment_amount is not None:
            payment_amount = validate_amount(amount=payment_amount)
            quest.payment_amount = payment_amount
        if max_completions is not None:
            quest.max_completions = max_completions
        if expires_at is not None:
            quest.expires_at = expires_at
        if requirements is not None:
            quest.requirements = requirements

        await quest.save()
        logger.info("🔄 Quest updated", quest_id=quest.id)
        return quest
    except Exception as e:
        logger.error("Failed to update quest", error=str(e), quest_id=quest.id)
        raise


async def cancel_quest(quest: Quest) -> Quest:
    """
    Cancel quest

    Args:
        quest: Quest instance to cancel

    Returns:
        Updated Quest instance

    Raises:
        Exception: If update fails
    """
    try:
        quest.status = QuestStatus.CANCELLED
        await quest.save()
        logger.info("❌ Quest cancelled", quest_id=quest.id)
        return quest
    except Exception as e:
        logger.error("Failed to cancel quest", error=str(e), quest_id=quest.id)
        raise


async def expire_quest(quest: Quest) -> Quest:
    """
    Mark quest as expired

    Args:
        quest: Quest instance to expire

    Returns:
        Updated Quest instance

    Raises:
        Exception: If update fails
    """
    try:
        quest.status = QuestStatus.EXPIRED
        await quest.save()
        logger.info("⏰ Quest expired", quest_id=quest.id)
        return quest
    except Exception as e:
        logger.error("Failed to expire quest", error=str(e), quest_id=quest.id)
        raise


# QuestProgress CRUD operations


async def start_quest(quest: Quest, player: Player) -> QuestProgress:
    """
    Start quest for player (create QuestProgress)

    Args:
        quest: Quest instance
        player: Player instance

    Returns:
        QuestProgress: Created progress instance

    Raises:
        ValueError: If quest is not active or already started
        Exception: If creation fails
    """
    if quest.status != QuestStatus.ACTIVE:
        raise ValueError("Quest is not active")

    now = datetime.now()
    if quest.expires_at and quest.expires_at < now:
        raise ValueError("Quest has expired")

    existing_progress = await QuestProgress.get_or_none(quest=quest, player=player)
    if existing_progress:
        raise ValueError("Quest already started by this player")

    try:
        progress = await QuestProgress.create(
            quest=quest,
            player=player,
            progress={},
            is_completed=False,
            claimed_reward=False,
        )
        logger.info(
            "🎯 Quest started",
            quest_id=quest.id,
            player_id=player.id,
            progress_id=progress.id,
        )
        return progress
    except Exception as e:
        logger.error(
            "Failed to start quest",
            error=str(e),
            quest_id=quest.id,
            player_id=player.id,
        )
        raise


async def get_quest_progress(quest: Quest, player: Player) -> Optional[QuestProgress]:
    """
    Get quest progress for player

    Args:
        quest: Quest instance
        player: Player instance

    Returns:
        QuestProgress or None if not found
    """
    try:
        return await QuestProgress.get_or_none(quest=quest, player=player)
    except Exception as e:
        logger.error(
            "Failed to get quest progress",
            error=str(e),
            quest_id=quest.id,
            player_id=player.id,
        )
        raise


async def get_player_quest_progress(
    player: Player,
    is_completed: Optional[bool] = None,
) -> List[QuestProgress]:
    """
    Get all quest progress for player

    Args:
        player: Player instance
        is_completed: Filter by completion status (optional)

    Returns:
        List of QuestProgress instances
    """
    try:
        query = QuestProgress.filter(player=player)
        if is_completed is not None:
            query = query.filter(is_completed=is_completed)
        return await query.all()
    except Exception as e:
        logger.error(
            "Failed to get player quest progress", error=str(e), player_id=player.id
        )
        raise


async def update_quest_progress(
    progress: QuestProgress,
    progress_data: Optional[Dict] = None,
) -> QuestProgress:
    """
    Update quest progress

    Args:
        progress: QuestProgress instance to update
        progress_data: New progress data (optional, merges with existing)

    Returns:
        Updated QuestProgress instance

    Raises:
        Exception: If update fails
    """
    try:
        if progress_data is not None:
            current_progress = progress.progress or {}
            current_progress.update(progress_data)
            progress.progress = current_progress

        await progress.save()
        logger.info("📊 Quest progress updated", progress_id=progress.id)
        return progress
    except Exception as e:
        logger.error(
            "Failed to update quest progress", error=str(e), progress_id=progress.id
        )
        raise


async def complete_quest(progress: QuestProgress) -> QuestProgress:
    """
    Mark quest as completed

    Args:
        progress: QuestProgress instance

    Returns:
        Updated QuestProgress instance

    Raises:
        ValueError: If quest is already completed
        Exception: If update fails
    """
    if progress.is_completed:
        raise ValueError("Quest is already completed")

    try:
        progress.is_completed = True
        progress.completed_at = datetime.now()

        # Update quest completion count
        quest = progress.quest
        quest.current_completions += 1

        # Check if quest reached max completions
        if quest.max_completions and quest.current_completions >= quest.max_completions:
            quest.status = QuestStatus.COMPLETED

        await quest.save()
        await progress.save()

        logger.info(
            "✅ Quest completed",
            progress_id=progress.id,
            quest_id=quest.id,
            player_id=progress.player.id,
        )
        return progress
    except Exception as e:
        logger.error("Failed to complete quest", error=str(e), progress_id=progress.id)
        raise


async def claim_quest_reward(progress: QuestProgress) -> QuestProgress:
    """
    Claim quest reward

    Args:
        progress: QuestProgress instance

    Returns:
        Updated QuestProgress instance

    Raises:
        ValueError: If quest is not completed or reward already claimed
        Exception: If update fails
    """
    from core.models.economics.transactions import Transaction, TransactionType

    try:
        async with in_transaction() as conn:
            locked_progress = (
                await QuestProgress.filter(id=progress.id)
                .using_db(conn)
                .select_for_update()
                .first()
            )
            if not locked_progress:
                raise ValueError("Quest progress not found")
            if not locked_progress.is_completed:
                raise ValueError("Quest is not completed")
            if locked_progress.claimed_reward:
                raise ValueError("Reward already claimed")

            await locked_progress.fetch_related("quest", "player")
            quest = locked_progress.quest
            player = locked_progress.player

            if quest.reward_amount > 0:
                locked_player = (
                    await Player.filter(id=player.id)
                    .using_db(conn)
                    .select_for_update()
                    .first()
                )
                if not locked_player:
                    raise ValueError("Player not found")

                locked_player.balance += quest.reward_amount
                await locked_player.save(update_fields=["balance"], using_db=conn)

                await Transaction.create(
                    from_player=None,
                    to_player=locked_player,
                    amount=quest.reward_amount,
                    transaction_type=TransactionType.QUEST_PAYMENT,
                    description=f"Quest reward: {quest.title}",
                    related_entity_type="quest",
                    related_entity_id=quest.id,
                    using_db=conn,
                )

            locked_progress.claimed_reward = True
            await locked_progress.save(update_fields=["claimed_reward"], using_db=conn)

        logger.info(
            "🎁 Quest reward claimed",
            progress_id=locked_progress.id,
            quest_id=quest.id,
            player_id=player.id,
            reward_amount=quest.reward_amount,
        )
        return locked_progress
    except Exception as e:
        logger.error(
            "Failed to claim quest reward", error=str(e), progress_id=progress.id
        )
        raise


async def delete_quest_progress(progress: QuestProgress) -> None:
    """
    Delete quest progress

    Args:
        progress: QuestProgress instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        progress_id = progress.id
        await progress.delete()
        logger.info("🗑️ Quest progress deleted", progress_id=progress_id)
    except Exception as e:
        logger.error(
            "Failed to delete quest progress", error=str(e), progress_id=progress_id
        )
        raise


async def get_quest_recommendations(player: Player, limit: int = 5) -> List[Quest]:
    """
    Get quest recommendations for player based on their progress and preferences

    Args:
        player: Player instance
        limit: Maximum number of recommendations (default: 5)

    Returns:
        List of recommended Quest instances
    """
    try:
        # Get active quests
        active_quests = await get_active_quests()

        # Get player's quest progress
        player_progresses = await get_player_quest_progress(player, is_completed=False)
        started_quest_ids = {qp.quest.id for qp in player_progresses}

        # Filter out quests player already started
        available_quests = [q for q in active_quests if q.id not in started_quest_ids]

        # Sort by reward amount (descending) and return top
        available_quests.sort(key=lambda x: x.reward_amount, reverse=True)

        return available_quests[:limit]
    except Exception as e:
        logger.error(
            "Failed to get quest recommendations", error=str(e), player_id=player.id
        )
        raise


async def get_player_quest_statistics(player: Player) -> Dict[str, Any]:
    """
    Get player quest statistics

    Args:
        player: Player instance

    Returns:
        Dictionary with quest statistics
    """
    try:
        from core.shared.utils import format_money

        progresses = await get_player_quest_progress(player)
        completed = [qp for qp in progresses if qp.is_completed]
        active = [qp for qp in progresses if not qp.is_completed]

        # Calculate total rewards
        total_rewards = sum(qp.quest.reward_amount for qp in completed)
        claimed_rewards = sum(
            qp.quest.reward_amount for qp in completed if qp.claimed_reward
        )

        return {
            "total_quests": len(progresses),
            "completed": len(completed),
            "active": len(active),
            "total_rewards": total_rewards,
            "claimed_rewards": claimed_rewards,
            "unclaimed_rewards": total_rewards - claimed_rewards,
            "completion_rate": (
                len(completed) / len(progresses) if len(progresses) > 0 else 0
            ),
        }
    except Exception as e:
        logger.error(
            "Failed to get player quest statistics", error=str(e), player_id=player.id
        )
        raise


async def search_quests(
    query: str, scenario_type: Optional[QuestType] = None
) -> List[Quest]:
    """
    Search quests by title or description

    Args:
        query: Search query
        scenario_type: Filter by quest type (optional)

    Returns:
        List of matching Quest instances
    """
    try:
        from core.shared.utils import search_by_name

        if scenario_type:
            quests = await get_active_quests(quest_type=scenario_type)
        else:
            quests = await get_active_quests()

        # Search in title and description
        matching = []
        query_lower = query.lower()
        for quest in quests:
            if (
                query_lower in quest.title.lower()
                or query_lower in quest.description.lower()
            ):
                matching.append(quest)

        return matching
    except Exception as e:
        logger.error("Failed to search quests", error=str(e), query=query)
        raise
