"""
Economics schemas for transactions and quests
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
from core.models.economics.transactions import TransactionType
from core.models.economics.quests import QuestType, QuestStatus


class BalanceResponse(BaseModel):
    """Баланс игрока"""

    balance: int
    frozen: int = 0


class DailyRewardResponse(BaseModel):
    """Ответ для daily-награды."""

    base_amount: int
    streak_days: int
    streak_max: int
    multiplier: float
    final_amount: int
    next_available_at: Optional[datetime] = None
    balance_after: int


class TransactionCreate(BaseModel):
    """Schema for creating a transaction"""

    amount: int
    transaction_type: TransactionType
    description: str
    from_player_id: Optional[int] = None
    to_player_id: Optional[int] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 1000,
                "transaction_type": "transfer",
                "description": "Payment for service",
                "from_player_id": 1,
                "to_player_id": 2,
            }
        }


class TransferCreate(BaseModel):
    """Schema for player-to-player transfer"""

    to_player_id: int
    amount: int
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "to_player_id": 2,
                "amount": 500,
                "description": "Guild support",
            }
        }


class TransferResponse(BaseModel):
    """Schema for transfer result"""

    transaction_id: int
    from_player_id: int
    to_player_id: int
    amount: int
    from_balance_after: int
    to_balance_after: int
    created_at: datetime


class TransactionResponse(BaseModel):
    """Schema for transaction response"""

    id: int
    from_player_id: Optional[int] = None
    to_player_id: Optional[int] = None
    amount: int
    transaction_type: str
    description: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    """Schema for filtering transactions"""

    from_player_id: Optional[int] = None
    to_player_id: Optional[int] = None
    transaction_type: Optional[TransactionType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    per_page: int = 20


class QuestCreate(BaseModel):
    """Schema for creating a quest"""

    title: str
    description: str
    quest_type: QuestType
    reward_amount: int = 0
    payment_amount: int = 0
    max_completions: Optional[int] = None
    expires_at: Optional[datetime] = None
    requirements: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Collect 10 diamonds",
                "description": "Collect 10 diamonds and bring them to the quest giver",
                "quest_type": "system",
                "reward_amount": 1000,
                "requirements": {"item_id": "minecraft:diamond", "quantity": 10},
            }
        }


class QuestResponse(BaseModel):
    """Schema for quest response"""

    id: int
    creator_id: Optional[int] = None
    title: str
    description: str
    quest_type: str
    reward_amount: int
    payment_amount: int
    status: str
    max_completions: Optional[int] = None
    current_completions: int
    expires_at: Optional[datetime] = None
    requirements: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestUpdate(BaseModel):
    """Schema for updating a quest"""

    title: Optional[str] = None
    description: Optional[str] = None
    reward_amount: Optional[int] = None
    payment_amount: Optional[int] = None
    max_completions: Optional[int] = None
    expires_at: Optional[datetime] = None
    requirements: Optional[Dict[str, Any]] = None


class QuestProgressResponse(BaseModel):
    """Schema for quest progress response"""

    id: int
    quest_id: int
    player_id: int
    progress: Dict[str, Any]
    is_completed: bool
    completed_at: Optional[datetime] = None
    claimed_reward: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestRecommendationResponse(BaseModel):
    """Schema for quest recommendation response"""

    quest: QuestResponse
    reason: str
