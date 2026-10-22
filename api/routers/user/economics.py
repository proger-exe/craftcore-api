"""
User economics router for transactions and quests
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from api.schemas.economics import (
    BalanceResponse,
    DailyRewardResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionFilter,
    TransferCreate,
    TransferResponse,
    QuestResponse,
    QuestProgressResponse,
)
from api.schemas.common import PaginatedResponse, SuccessResponse
from api.dependencies import get_current_player, validate_pagination
from api.routers.user.daily import process_daily_reward
from core.models.players.players import Player
from core.models.economics.transactions import TransactionType
from core.models.economics.quests import QuestType
from core.managers.economics.transactions import (
    create_transaction,
    transfer_between_players,
    get_transaction,
    get_player_transactions,
    get_transactions,
    get_player_balance_history,
    get_top_players_by_balance,
)
from core.managers.economics.quests import (
    get_quest,
    get_active_quests,
    get_quest_recommendations,
    get_player_quest_statistics,
    search_quests,
    start_quest,
    get_quest_progress,
    complete_quest,
    claim_quest_reward,
)
from core.managers.players.players import get_player as get_player_by_id
from core.managers.players.profile import get_player_profile
from core.shared.errors import (
    NotFoundError,
    ForbiddenError,
    InsufficientBalanceError,
    ValidationError,
)

router = APIRouter(prefix="/user", tags=["user", "economics"])


@router.get("/balance", response_model=BalanceResponse)
async def get_balance_endpoint(player: Player = Depends(get_current_player)):
    """Получить баланс текущего игрока"""
    frozen = getattr(player, "frozen_balance", 0)
    return BalanceResponse(balance=player.balance, frozen=frozen)


@router.post("/economics/daily", response_model=DailyRewardResponse)
async def daily_reward_compat_endpoint(player: Player = Depends(get_current_player)):
    """Совместимость: старый путь daily-награды."""
    return await process_daily_reward(player)


# Transaction endpoints


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions_endpoint(
    transaction_type: Optional[TransactionType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get player transactions with filters"""
    pagination = validate_pagination(page=page, per_page=per_page)
    transactions = await get_player_transactions(
        player=player,
        as_sender=True,
        as_receiver=True,
        limit=pagination["per_page"],
        offset=(pagination["page"] - 1) * pagination["per_page"],
    )

    # Apply additional filters
    if transaction_type:
        transactions = [
            t for t in transactions if t.transaction_type == transaction_type
        ]
    if start_date:
        transactions = [t for t in transactions if t.created_at >= start_date]
    if end_date:
        transactions = [t for t in transactions if t.created_at <= end_date]

    return [TransactionResponse.model_validate(t) for t in transactions]


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_endpoint(
    transaction_id: int, player: Player = Depends(get_current_player)
):
    """Get transaction by ID"""
    transaction = await get_transaction(transaction_id)
    if not transaction:
        raise NotFoundError("Transaction not found")

    # Check if player is involved in transaction
    if (
        transaction.from_player
        and transaction.from_player.id != player.id
        and transaction.to_player
        and transaction.to_player.id != player.id
    ):
        raise ForbiddenError("Access denied")

    return TransactionResponse.model_validate(transaction)


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction_endpoint(
    transaction_data: TransactionCreate, player: Player = Depends(get_current_player)
):
    """Create a new transaction"""
    from_player = None
    to_player = None

    if transaction_data.from_player_id:
        from_player = await get_player_by_id(transaction_data.from_player_id)
        if not from_player:
            raise NotFoundError("From player not found")
        if from_player.id != player.id:
            raise ForbiddenError("Cannot create transaction for other player")

    if transaction_data.to_player_id:
        to_player = await get_player_by_id(transaction_data.to_player_id)
        if not to_player:
            raise NotFoundError("To player not found")

    transaction = await create_transaction(
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        description=transaction_data.description,
        from_player=from_player or player,
        to_player=to_player,
        related_entity_type=transaction_data.related_entity_type,
        related_entity_id=transaction_data.related_entity_id,
    )

    return TransactionResponse.model_validate(transaction)


@router.post("/transactions/transfer", response_model=TransferResponse, status_code=201)
async def transfer_between_players_endpoint(
    transfer_data: TransferCreate, player: Player = Depends(get_current_player)
):
    """Transfer vaysh from current player to another player"""
    to_player = await get_player_by_id(transfer_data.to_player_id)
    if not to_player:
        raise NotFoundError("To player not found")

    # Transfer target must have a profile in system
    to_profile = await get_player_profile(to_player)
    if not to_profile:
        raise NotFoundError("To player profile not found")

    try:
        result = await transfer_between_players(
            from_player=player,
            to_player=to_player,
            amount=transfer_data.amount,
            description=transfer_data.description,
        )
    except ValueError as e:
        error_text = str(e)
        if "Insufficient balance" in error_text:
            raise InsufficientBalanceError(error_text)
        raise ValidationError(error_text)

    transaction = result["transaction"]
    return TransferResponse(
        transaction_id=transaction.id,
        from_player_id=player.id,
        to_player_id=to_player.id,
        amount=transaction.amount,
        from_balance_after=result["from_balance_after"],
        to_balance_after=result["to_balance_after"],
        created_at=transaction.created_at,
    )


@router.get("/transactions/balance-history")
async def get_balance_history_endpoint(
    days: int = Query(30, ge=1, le=365),
    player: Player = Depends(get_current_player),
):
    """Get player balance history"""
    return await get_player_balance_history(player, days=days)


@router.get("/transactions/top-players", response_model=List[dict])
async def get_top_players_endpoint(
    limit: int = Query(10, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get top players by balance"""
    top_players = await get_top_players_by_balance(limit=limit)
    return [
        {
            "id": p.id,
            "nickname": p.nickname,
            "balance": p.balance,
        }
        for p in top_players
    ]


# Quest endpoints


@router.get("/quests", response_model=List[QuestResponse])
async def get_quests_endpoint(
    quest_type: Optional[QuestType] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get active quests"""
    pagination = validate_pagination(page=page, per_page=per_page)

    if search:
        quests = await search_quests(query=search, scenario_type=quest_type)
    else:
        quests = await get_active_quests(
            quest_type=quest_type,
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )

    return [QuestResponse.model_validate(q) for q in quests]


@router.get("/quests/{quest_id}", response_model=QuestResponse)
async def get_quest_endpoint(
    quest_id: int, player: Player = Depends(get_current_player)
):
    """Get quest by ID"""
    quest = await get_quest(quest_id)
    if not quest:
        raise NotFoundError("Quest not found")
    return QuestResponse.model_validate(quest)


@router.get("/quests/recommendations", response_model=List[QuestResponse])
async def get_quest_recommendations_endpoint(
    limit: int = Query(5, ge=1, le=20),
    player: Player = Depends(get_current_player),
):
    """Get quest recommendations for player"""
    recommendations = await get_quest_recommendations(player, limit=limit)
    return [QuestResponse.model_validate(q) for q in recommendations]


@router.get("/quests/statistics")
async def get_quest_statistics_endpoint(
    player: Player = Depends(get_current_player),
):
    """Get player quest statistics"""
    return await get_player_quest_statistics(player)


@router.post(
    "/quests/{quest_id}/start", response_model=QuestProgressResponse, status_code=201
)
async def start_quest_endpoint(
    quest_id: int, player: Player = Depends(get_current_player)
):
    """Start a quest"""
    quest = await get_quest(quest_id)
    if not quest:
        raise NotFoundError("Quest not found")

    try:
        progress = await start_quest(quest=quest, player=player)
    except ValueError as e:
        raise ValidationError(str(e))
    return QuestProgressResponse.model_validate(progress)


@router.get("/quests/{quest_id}/progress", response_model=QuestProgressResponse)
async def get_quest_progress_endpoint(
    quest_id: int, player: Player = Depends(get_current_player)
):
    """Get quest progress for player"""
    quest = await get_quest(quest_id)
    if not quest:
        raise NotFoundError("Quest not found")

    progress = await get_quest_progress(quest=quest, player=player)
    if not progress:
        raise NotFoundError("Quest progress not found")

    return QuestProgressResponse.model_validate(progress)


@router.post("/quests/{quest_id}/complete", response_model=QuestProgressResponse)
async def complete_quest_endpoint(
    quest_id: int, player: Player = Depends(get_current_player)
):
    """Complete a quest"""
    quest = await get_quest(quest_id)
    if not quest:
        raise NotFoundError("Quest not found")

    progress = await get_quest_progress(quest=quest, player=player)
    if not progress:
        raise NotFoundError("Quest progress not found")

    try:
        completed = await complete_quest(progress=progress)
    except ValueError as e:
        raise ValidationError(str(e))
    return QuestProgressResponse.model_validate(completed)


@router.post("/quests/{quest_id}/claim", response_model=QuestProgressResponse)
async def claim_quest_reward_endpoint(
    quest_id: int, player: Player = Depends(get_current_player)
):
    """Claim quest reward"""
    quest = await get_quest(quest_id)
    if not quest:
        raise NotFoundError("Quest not found")

    progress = await get_quest_progress(quest=quest, player=player)
    if not progress:
        raise NotFoundError("Quest progress not found")

    try:
        claimed = await claim_quest_reward(progress=progress)
    except ValueError as e:
        raise ValidationError(str(e))
    return QuestProgressResponse.model_validate(claimed)
