"""User player-created quests marketplace endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_current_player
from api.schemas.common import SuccessResponse
from api.schemas.player_quests import (
    PlayerQuestApplicationCreate,
    PlayerQuestApplicationResponse,
    PlayerQuestCreate,
    PlayerQuestResponse,
    PlayerQuestReviewRequest,
    PlayerQuestSubmissionRequest,
)
from core.managers.economics.player_quests import (
    abandon_player_quest,
    accept_player_quest_application,
    approve_player_quest,
    cancel_player_quest,
    create_player_quest,
    create_player_quest_application,
    delete_player_quest,
    get_player_quest,
    list_my_player_quest_applications,
    list_player_quest_applications,
    list_player_quests,
    reject_player_quest_application,
    request_player_quest_changes,
    submit_player_quest_result,
    withdraw_player_quest_application,
)
from core.models.players.players import Player
from core.shared.errors import ForbiddenError, NotFoundError

router = APIRouter(prefix="/user", tags=["user", "player-quests"])

APPLICATION_ACTIVE_STATUSES = {"applied", "accepted", "submitted", "changes_requested"}


def _active_application_for_quest(pq):
    applications = list(getattr(pq, "applications", []) or [])
    if pq.executor_id is not None:
        for application in applications:
            if application.applicant_id == pq.executor_id:
                return application
    for status in ("submitted", "changes_requested", "accepted", "completed"):
        for application in applications:
            if application.status == status:
                return application
    return None


def _my_application(pq, player_id: int):
    applications = [
        application
        for application in (getattr(pq, "applications", []) or [])
        if application.applicant_id == player_id
    ]
    if not applications:
        return None
    applications.sort(key=lambda item: (item.updated_at, item.created_at), reverse=True)
    return applications[0]


def _pq_to_response(pq, player: Player) -> PlayerQuestResponse:
    applications = list(getattr(pq, "applications", []) or [])
    active_application = _active_application_for_quest(pq)
    my_application = _my_application(pq, player.id)

    can_apply = (
        pq.creator_id != player.id
        and pq.status == "open"
        and (
            my_application is None
            or my_application.status not in APPLICATION_ACTIVE_STATUSES
        )
    )
    can_view_applications = pq.creator_id == player.id
    can_cancel = pq.creator_id == player.id and pq.status not in {
        "completed",
        "cancelled",
        "deleted",
    }
    can_delete = (
        pq.creator_id == player.id
        and pq.executor_id is None
        and pq.status in {"open", "cancelled"}
    )
    can_submit = (
        pq.executor_id == player.id
        and pq.status in {"in_progress", "changes_requested"}
        and my_application is not None
        and my_application.status in {"accepted", "changes_requested"}
    )
    can_approve = pq.creator_id == player.id and pq.status == "pending_review"
    can_request_changes = can_approve
    can_abandon = pq.executor_id == player.id and pq.status in {
        "in_progress",
        "pending_review",
        "changes_requested",
    }

    return PlayerQuestResponse(
        id=pq.id,
        creator_id=pq.creator_id,
        title=pq.title,
        description=pq.description,
        reward=pq.reward,
        status=pq.status,
        executor_id=pq.executor_id,
        applications_count=len(applications),
        my_application_status=my_application.status if my_application else None,
        submission_message=(
            active_application.submission_message if active_application else None
        ),
        review_comment=active_application.review_comment if active_application else None,
        created_at=pq.created_at,
        updated_at=pq.updated_at,
        can_apply=can_apply,
        can_view_applications=can_view_applications,
        can_cancel=can_cancel,
        can_delete=can_delete,
        can_submit=can_submit,
        can_approve=can_approve,
        can_request_changes=can_request_changes,
        can_abandon=can_abandon,
    )


def _application_to_response(application) -> PlayerQuestApplicationResponse:
    quest = getattr(application, "quest", None)
    return PlayerQuestApplicationResponse(
        id=application.id,
        quest_id=application.quest_id,
        applicant_id=application.applicant_id,
        status=application.status,
        cover_letter=application.cover_letter,
        submission_message=application.submission_message,
        review_comment=application.review_comment,
        created_at=application.created_at,
        updated_at=application.updated_at,
        quest_title=quest.title if quest else None,
    )


@router.post("/quests/create", response_model=PlayerQuestResponse, status_code=201)
async def create_player_quest_endpoint(
    body: PlayerQuestCreate,
    player: Player = Depends(get_current_player),
):
    quest = await create_player_quest(
        creator=player,
        title=body.title,
        description=body.description,
        reward=body.reward,
    )
    return _pq_to_response(quest, player)


@router.get(
    "/quests/applications/mine",
    response_model=list[PlayerQuestApplicationResponse],
)
async def list_my_player_quest_applications_endpoint(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    player: Player = Depends(get_current_player),
):
    applications = await list_my_player_quest_applications(
        applicant=player,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_application_to_response(application) for application in applications]


@router.get("/quests/player-created", response_model=list[PlayerQuestResponse])
async def list_player_quests_endpoint(
    creator_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    player: Player = Depends(get_current_player),
):
    quests = await list_player_quests(
        creator_id=creator_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_pq_to_response(quest, player) for quest in quests]


@router.get("/quests/{quest_id}", response_model=PlayerQuestResponse)
async def get_player_quest_endpoint(
    quest_id: int,
    player: Player = Depends(get_current_player),
):
    quest = await get_player_quest(quest_id)
    if not quest:
        raise NotFoundError("Quest not found")
    return _pq_to_response(quest, player)


@router.post(
    "/quests/{quest_id}/applications",
    response_model=PlayerQuestApplicationResponse,
    status_code=201,
)
async def create_player_quest_application_endpoint(
    quest_id: int,
    body: PlayerQuestApplicationCreate,
    player: Player = Depends(get_current_player),
):
    application = await create_player_quest_application(
        quest_id=quest_id,
        applicant=player,
        cover_letter=body.cover_letter,
    )
    return _application_to_response(application)


@router.get(
    "/quests/{quest_id}/applications",
    response_model=list[PlayerQuestApplicationResponse],
)
async def list_player_quest_applications_endpoint(
    quest_id: int,
    player: Player = Depends(get_current_player),
):
    quest = await get_player_quest(quest_id)
    if not quest:
        raise NotFoundError("Quest not found")
    if quest.creator_id != player.id:
        raise ForbiddenError("Only creator can view applications")
    applications = await list_player_quest_applications(quest_id)
    return [_application_to_response(application) for application in applications]


@router.post(
    "/quests/{quest_id}/applications/{application_id}/accept",
    response_model=PlayerQuestResponse,
)
async def accept_player_quest_application_endpoint(
    quest_id: int,
    application_id: int,
    player: Player = Depends(get_current_player),
):
    quest = await accept_player_quest_application(quest_id, application_id, player)
    return _pq_to_response(quest, player)


@router.post(
    "/quests/{quest_id}/applications/{application_id}/reject",
    response_model=PlayerQuestApplicationResponse,
)
async def reject_player_quest_application_endpoint(
    quest_id: int,
    application_id: int,
    body: PlayerQuestReviewRequest,
    player: Player = Depends(get_current_player),
):
    application = await reject_player_quest_application(
        quest_id=quest_id,
        application_id=application_id,
        owner=player,
        comment=body.comment,
    )
    return _application_to_response(application)


@router.post(
    "/quests/{quest_id}/applications/{application_id}/withdraw",
    response_model=PlayerQuestApplicationResponse,
)
async def withdraw_player_quest_application_endpoint(
    quest_id: int,
    application_id: int,
    player: Player = Depends(get_current_player),
):
    application = await withdraw_player_quest_application(
        quest_id=quest_id,
        application_id=application_id,
        applicant=player,
    )
    return _application_to_response(application)


@router.post("/quests/{quest_id}/submit", response_model=PlayerQuestResponse)
async def submit_player_quest_result_endpoint(
    quest_id: int,
    body: PlayerQuestSubmissionRequest,
    player: Player = Depends(get_current_player),
):
    quest = await submit_player_quest_result(
        quest_id=quest_id,
        executor=player,
        submission_message=body.submission_message,
    )
    return _pq_to_response(quest, player)


@router.post("/quests/{quest_id}/approve", response_model=PlayerQuestResponse)
async def approve_player_quest_endpoint(
    quest_id: int,
    player: Player = Depends(get_current_player),
):
    quest = await approve_player_quest(quest_id=quest_id, owner=player)
    return _pq_to_response(quest, player)


@router.post("/quests/{quest_id}/request-changes", response_model=PlayerQuestResponse)
async def request_player_quest_changes_endpoint(
    quest_id: int,
    body: PlayerQuestReviewRequest,
    player: Player = Depends(get_current_player),
):
    quest = await request_player_quest_changes(
        quest_id=quest_id,
        owner=player,
        comment=body.comment,
    )
    return _pq_to_response(quest, player)


@router.post("/quests/{quest_id}/abandon", response_model=PlayerQuestResponse)
async def abandon_player_quest_endpoint(
    quest_id: int,
    player: Player = Depends(get_current_player),
):
    quest = await abandon_player_quest(quest_id=quest_id, executor=player)
    return _pq_to_response(quest, player)


@router.post("/quests/{quest_id}/cancel", response_model=PlayerQuestResponse)
async def cancel_player_quest_endpoint(
    quest_id: int,
    player: Player = Depends(get_current_player),
):
    quest = await cancel_player_quest(quest_id=quest_id, owner=player)
    return _pq_to_response(quest, player)


@router.delete("/quests/{quest_id}", response_model=SuccessResponse)
async def delete_player_quest_endpoint(
    quest_id: int,
    player: Player = Depends(get_current_player),
):
    await delete_player_quest(quest_id=quest_id, owner=player)
    return SuccessResponse(message="Quest deleted successfully")
