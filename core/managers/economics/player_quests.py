"""Marketplace workflow for player-created quests."""

from typing import List, Optional

from tortoise import timezone
from tortoise.transactions import in_transaction

from core.managers.economics.utils import validate_amount
from core.models.economics.player_quests import PlayerQuest, PlayerQuestApplication
from core.models.economics.transactions import Transaction, TransactionType
from core.models.players.players import Player
from core.shared.errors import ForbiddenError, NotFoundError, ValidationError
from core.shared.logger import logger

QUEST_OPEN_STATUSES = {"open"}
QUEST_EXECUTOR_ACTIVE_STATUSES = {"in_progress", "pending_review", "changes_requested"}
QUEST_FINAL_STATUSES = {"completed", "cancelled", "deleted"}
APPLICATION_FINAL_STATUSES = {"rejected", "withdrawn", "completed", "cancelled"}
APPLICATION_ACTIVE_STATUSES = {"applied", "accepted", "submitted", "changes_requested"}


async def create_player_quest(
    creator: Player,
    title: str,
    description: str,
    reward: int,
) -> PlayerQuest:
    """Create a quest and freeze reward on the creator wallet."""
    reward = validate_amount(reward)
    if reward < 1:
        raise ValidationError("Reward must be positive")

    from core.managers.players.players import freeze_player_balance

    await freeze_player_balance(creator, reward, reason="player_quest_reward")
    quest = await PlayerQuest.create(
        creator=creator,
        title=title,
        description=description,
        reward=reward,
        status="open",
    )
    logger.info(
        "Player quest created",
        quest_id=quest.id,
        creator_id=creator.id,
        reward=reward,
    )
    return await get_player_quest(quest.id)


async def list_player_quests(
    creator_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[PlayerQuest]:
    qs = (
        PlayerQuest.all()
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
        .prefetch_related("creator", "executor", "applications")
    )
    if creator_id is not None:
        qs = qs.filter(creator_id=creator_id)
    if status:
        qs = qs.filter(status=status)
    return await qs


async def list_my_player_quest_applications(
    applicant: Player,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[PlayerQuestApplication]:
    qs = (
        PlayerQuestApplication.filter(applicant_id=applicant.id)
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
        .prefetch_related("quest")
    )
    if status:
        qs = qs.filter(status=status)
    return await qs


async def get_player_quest(quest_id: int) -> Optional[PlayerQuest]:
    return await (
        PlayerQuest.get_or_none(id=quest_id)
        .prefetch_related("creator", "executor", "applications__applicant")
    )


async def get_player_quest_application(
    application_id: int,
) -> Optional[PlayerQuestApplication]:
    return await PlayerQuestApplication.get_or_none(id=application_id).prefetch_related(
        "quest", "applicant"
    )


async def create_player_quest_application(
    quest_id: int,
    applicant: Player,
    cover_letter: Optional[str],
) -> PlayerQuestApplication:
    async with in_transaction() as conn:
        quest = (
            await PlayerQuest.filter(id=quest_id)
            .using_db(conn)
            .select_for_update()
            .first()
        )
        if not quest:
            raise NotFoundError("Quest not found")
        if quest.creator_id == applicant.id:
            raise ValidationError("Cannot apply to your own quest")
        if quest.status != "open":
            raise ValidationError("Quest is not open for applications")

        existing = await (
            PlayerQuestApplication.filter(quest_id=quest_id, applicant_id=applicant.id)
            .using_db(conn)
            .all()
        )
        if any(app.status in APPLICATION_ACTIVE_STATUSES for app in existing):
            raise ValidationError("Active application already exists")

        application = await PlayerQuestApplication.create(
            quest_id=quest_id,
            applicant_id=applicant.id,
            status="applied",
            cover_letter=cover_letter,
            using_db=conn,
        )

    logger.info(
        "Player quest application created",
        quest_id=quest_id,
        application_id=application.id,
        applicant_id=applicant.id,
    )
    return await get_player_quest_application(application.id)


async def list_player_quest_applications(
    quest_id: int,
) -> List[PlayerQuestApplication]:
    return await (
        PlayerQuestApplication.filter(quest_id=quest_id)
        .order_by("-created_at")
        .prefetch_related("quest", "applicant")
    )


async def accept_player_quest_application(
    quest_id: int,
    application_id: int,
    owner: Player,
) -> PlayerQuest:
    async with in_transaction() as conn:
        quest = await _get_locked_quest(conn, quest_id)
        if quest.creator_id != owner.id:
            raise ForbiddenError("Only creator can accept applications")
        if quest.status != "open":
            raise ValidationError("Quest is not open")

        application = await _get_locked_application(conn, application_id, quest_id)
        if application.status != "applied":
            raise ValidationError("Application is not pending")

        quest.status = "in_progress"
        quest.executor_id = application.applicant_id
        await quest.save(
            update_fields=["status", "executor_id", "updated_at"], using_db=conn
        )

        application.status = "accepted"
        application.review_comment = None
        await application.save(
            update_fields=["status", "review_comment", "updated_at"], using_db=conn
        )

        await (
            PlayerQuestApplication.filter(
                quest_id=quest_id, status="applied"
            )
            .exclude(id=application_id)
            .using_db(conn)
            .update(status="rejected", updated_at=timezone.now())
        )

    logger.info(
        "Player quest application accepted",
        quest_id=quest_id,
        application_id=application_id,
        owner_id=owner.id,
        executor_id=application.applicant_id,
    )
    return await get_player_quest(quest_id)


async def reject_player_quest_application(
    quest_id: int,
    application_id: int,
    owner: Player,
    comment: Optional[str],
) -> PlayerQuestApplication:
    async with in_transaction() as conn:
        quest = await _get_locked_quest(conn, quest_id)
        if quest.creator_id != owner.id:
            raise ForbiddenError("Only creator can reject applications")

        application = await _get_locked_application(conn, application_id, quest_id)
        if application.status != "applied":
            raise ValidationError("Only pending applications can be rejected")

        application.status = "rejected"
        application.review_comment = comment
        await application.save(
            update_fields=["status", "review_comment", "updated_at"], using_db=conn
        )

    logger.info(
        "Player quest application rejected",
        quest_id=quest_id,
        application_id=application_id,
        owner_id=owner.id,
    )
    return await get_player_quest_application(application_id)


async def withdraw_player_quest_application(
    quest_id: int,
    application_id: int,
    applicant: Player,
) -> PlayerQuestApplication:
    async with in_transaction() as conn:
        application = await _get_locked_application(conn, application_id, quest_id)
        if application.applicant_id != applicant.id:
            raise ForbiddenError("Only applicant can withdraw application")
        if application.status != "applied":
            raise ValidationError("Only pending applications can be withdrawn")

        application.status = "withdrawn"
        await application.save(update_fields=["status", "updated_at"], using_db=conn)

    logger.info(
        "Player quest application withdrawn",
        quest_id=quest_id,
        application_id=application_id,
        applicant_id=applicant.id,
    )
    return await get_player_quest_application(application_id)


async def submit_player_quest_result(
    quest_id: int,
    executor: Player,
    submission_message: Optional[str],
) -> PlayerQuest:
    async with in_transaction() as conn:
        quest = await _get_locked_quest(conn, quest_id)
        if quest.executor_id != executor.id:
            raise ForbiddenError("Only accepted executor can submit result")
        if quest.status not in {"in_progress", "changes_requested"}:
            raise ValidationError("Quest is not ready for submission")

        application = await _get_executor_application(conn, quest)
        if application.status not in {"accepted", "changes_requested"}:
            raise ValidationError("Application is not ready for submission")

        quest.status = "pending_review"
        await quest.save(update_fields=["status", "updated_at"], using_db=conn)

        application.status = "submitted"
        application.submission_message = submission_message
        await application.save(
            update_fields=["status", "submission_message", "updated_at"], using_db=conn
        )

    logger.info("Player quest submitted", quest_id=quest_id, executor_id=executor.id)
    return await get_player_quest(quest_id)


async def approve_player_quest(
    quest_id: int,
    owner: Player,
) -> PlayerQuest:
    async with in_transaction() as conn:
        quest = await _get_locked_quest(conn, quest_id)
        if quest.creator_id != owner.id:
            raise ForbiddenError("Only creator can approve quest")
        if quest.status != "pending_review":
            raise ValidationError("Quest is not pending review")
        if not quest.executor_id:
            raise ValidationError("Quest has no executor")

        application = await _get_executor_application(conn, quest)
        if application.status != "submitted":
            raise ValidationError("No submitted work to approve")

        locked_players = await _lock_players(conn, [quest.creator_id, quest.executor_id])
        creator = locked_players[quest.creator_id]
        executor = locked_players[quest.executor_id]
        if creator.frozen_balance < quest.reward:
            raise ValidationError("Frozen reward is insufficient")
        if creator.balance < quest.reward:
            raise ValidationError("Creator balance is insufficient")

        creator.frozen_balance -= quest.reward
        creator.balance -= quest.reward
        executor.balance += quest.reward

        await creator.save(
            update_fields=["balance", "frozen_balance"], using_db=conn
        )
        await executor.save(update_fields=["balance"], using_db=conn)

        await Transaction.create(
            from_player=creator,
            to_player=executor,
            amount=quest.reward,
            transaction_type=TransactionType.QUEST_PAYMENT,
            description=f"Player quest payment #{quest.id}",
            related_entity_type="player_quest",
            related_entity_id=quest.id,
            using_db=conn,
        )

        quest.status = "completed"
        await quest.save(update_fields=["status", "updated_at"], using_db=conn)

        application.status = "completed"
        await application.save(update_fields=["status", "updated_at"], using_db=conn)

    logger.info("Player quest approved", quest_id=quest_id, owner_id=owner.id)
    return await get_player_quest(quest_id)


async def request_player_quest_changes(
    quest_id: int,
    owner: Player,
    comment: Optional[str],
) -> PlayerQuest:
    async with in_transaction() as conn:
        quest = await _get_locked_quest(conn, quest_id)
        if quest.creator_id != owner.id:
            raise ForbiddenError("Only creator can request changes")
        if quest.status != "pending_review":
            raise ValidationError("Quest is not pending review")

        application = await _get_executor_application(conn, quest)
        if application.status != "submitted":
            raise ValidationError("No submitted work to review")

        quest.status = "changes_requested"
        await quest.save(update_fields=["status", "updated_at"], using_db=conn)

        application.status = "changes_requested"
        application.review_comment = comment
        await application.save(
            update_fields=["status", "review_comment", "updated_at"], using_db=conn
        )

    logger.info(
        "Player quest changes requested", quest_id=quest_id, owner_id=owner.id
    )
    return await get_player_quest(quest_id)


async def abandon_player_quest(
    quest_id: int,
    executor: Player,
) -> PlayerQuest:
    async with in_transaction() as conn:
        quest = await _get_locked_quest(conn, quest_id)
        if quest.executor_id != executor.id:
            raise ForbiddenError("Only current executor can abandon quest")
        if quest.status not in QUEST_EXECUTOR_ACTIVE_STATUSES:
            raise ValidationError("Quest cannot be abandoned in current state")

        application = await _get_executor_application(conn, quest)
        if application.status not in {"accepted", "submitted", "changes_requested"}:
            raise ValidationError("Application cannot be abandoned in current state")

        quest.status = "open"
        quest.executor_id = None
        await quest.save(
            update_fields=["status", "executor_id", "updated_at"], using_db=conn
        )

        application.status = "withdrawn"
        await application.save(update_fields=["status", "updated_at"], using_db=conn)

    logger.info("Player quest abandoned", quest_id=quest_id, executor_id=executor.id)
    return await get_player_quest(quest_id)


async def cancel_player_quest(
    quest_id: int,
    owner: Player,
) -> PlayerQuest:
    async with in_transaction() as conn:
        quest = await _get_locked_quest(conn, quest_id)
        if quest.creator_id != owner.id:
            raise ForbiddenError("Only creator can cancel quest")
        if quest.status in {"completed", "deleted"}:
            raise ValidationError("Completed or deleted quest cannot be cancelled")
        if quest.status == "cancelled":
            raise ValidationError("Quest is already cancelled")

        locked_creator = (await _lock_players(conn, [quest.creator_id]))[quest.creator_id]
        if locked_creator.frozen_balance < quest.reward:
            raise ValidationError("Frozen reward is insufficient")

        locked_creator.frozen_balance -= quest.reward
        await locked_creator.save(update_fields=["frozen_balance"], using_db=conn)

        quest.status = "cancelled"
        quest.executor_id = None
        await quest.save(
            update_fields=["status", "executor_id", "updated_at"], using_db=conn
        )

        await (
            PlayerQuestApplication.filter(
                quest_id=quest_id, status__in=list(APPLICATION_ACTIVE_STATUSES)
            )
            .using_db(conn)
            .update(status="cancelled", updated_at=timezone.now())
        )

    logger.info("Player quest cancelled", quest_id=quest_id, owner_id=owner.id)
    return await get_player_quest(quest_id)


async def delete_player_quest(
    quest_id: int,
    owner: Player,
) -> PlayerQuest:
    async with in_transaction() as conn:
        quest = await _get_locked_quest(conn, quest_id)
        if quest.creator_id != owner.id:
            raise ForbiddenError("Only creator can delete quest")
        if quest.executor_id is not None:
            raise ValidationError("Quest with active executor cannot be deleted")
        if quest.status not in {"open", "cancelled"}:
            raise ValidationError("Quest can be deleted only from open or cancelled state")

        if quest.status == "open":
            locked_creator = (
                await _lock_players(conn, [quest.creator_id])
            )[quest.creator_id]
            if locked_creator.frozen_balance < quest.reward:
                raise ValidationError("Frozen reward is insufficient")
            locked_creator.frozen_balance -= quest.reward
            await locked_creator.save(update_fields=["frozen_balance"], using_db=conn)

            await (
                PlayerQuestApplication.filter(
                    quest_id=quest_id, status__in=list(APPLICATION_ACTIVE_STATUSES)
                )
                .using_db(conn)
                .update(status="cancelled", updated_at=timezone.now())
            )

        quest.status = "deleted"
        await quest.save(update_fields=["status", "updated_at"], using_db=conn)

    logger.info("Player quest deleted", quest_id=quest_id, owner_id=owner.id)
    return quest


async def _get_locked_quest(conn, quest_id: int) -> PlayerQuest:
    quest = (
        await PlayerQuest.filter(id=quest_id).using_db(conn).select_for_update().first()
    )
    if not quest:
        raise NotFoundError("Quest not found")
    return quest


async def _get_locked_application(
    conn,
    application_id: int,
    quest_id: int,
) -> PlayerQuestApplication:
    application = (
        await PlayerQuestApplication.filter(id=application_id, quest_id=quest_id)
        .using_db(conn)
        .select_for_update()
        .first()
    )
    if not application:
        raise NotFoundError("Application not found")
    return application


async def _get_executor_application(conn, quest: PlayerQuest) -> PlayerQuestApplication:
    application = (
        await PlayerQuestApplication.filter(
            quest_id=quest.id,
            applicant_id=quest.executor_id,
            status__in=["accepted", "submitted", "changes_requested", "completed"],
        )
        .using_db(conn)
        .select_for_update()
        .order_by("-updated_at")
        .first()
    )
    if not application:
        raise NotFoundError("Executor application not found")
    return application


async def _lock_players(conn, player_ids: List[int]) -> dict[int, Player]:
    locked_players = (
        await Player.filter(id__in=sorted(set(int(pid) for pid in player_ids)))
        .using_db(conn)
        .select_for_update()
        .all()
    )
    return {int(player.id): player for player in locked_players}
