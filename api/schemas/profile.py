"""
Player profile schemas
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from core.models.players.players import (
    PlayerGender,
    PlayerSource,
    EraStamp,
    PlayerWorldRating,
)


class PlayerProfileResponse(BaseModel):
    """Schema for player profile response. player_id is string to avoid JSON bigint precision loss in clients."""

    id: int
    player_id: str  # string so clients (e.g. JS) don't corrupt id; use as X-Player-ID
    nickname: str
    age: int
    gender: str
    source: str

    class Config:
        from_attributes = True


class PlayerProfileCreate(BaseModel):
    """Schema for creating player profile

    System will automatically create a Player with auto-generated ID.
    You can optionally provide tg_id or ds_id to link with external systems.
    Nickname is required and must be non-empty (used for creation by nickname only).
    """

    nickname: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="Nickname (required for creation by nickname only)",
    )
    age: Optional[int] = None
    gender: Optional[PlayerGender] = None
    source: Optional[str] = None
    tg_id: Optional[int] = None
    ds_id: Optional[str] = None

    @field_validator("nickname", mode="before")
    @classmethod
    def strip_nickname(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class PlayerProfileUpdate(BaseModel):
    """Schema for updating player profile"""

    nickname: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[PlayerGender] = None
    source: Optional[str] = None


class PlayerAnalyticsResponse(BaseModel):
    """Schema for player analytics response"""

    id: int
    player_id: int
    hours_played: int
    invites_count: int
    socials: Dict[str, str]
    world_rating: Optional[str] = None
    clan_id: Optional[int] = None
    party_id: Optional[int] = None
    earned_money: int
    spent_money: int
    bio: Optional[str] = None
    era_stamp: Optional[str] = None
    join_streak_days: int
    join_streak_max: int
    last_login: Optional[datetime] = None
    in_war: bool

    class Config:
        from_attributes = True


class PlayerAnalyticsUpdate(BaseModel):
    """Schema for updating player analytics"""

    bio: Optional[str] = None
    world_rating: Optional[PlayerWorldRating] = None
    era_stamp: Optional[EraStamp] = None
    # Плагин JustSocial пишет эти три поля при каждом PlayerJoinEvent (последний вход
    # + серия дней). Без них PUT /user/analytics молча дропал их, и /daily-гейт
    # никогда бы не пропускал живого игрока. См. PlayerJoinListener.updateJoinStreak.
    last_login: Optional[datetime] = None
    join_streak_days: Optional[int] = None
    join_streak_max: Optional[int] = None


class SocialLinkAdd(BaseModel):
    """Schema for adding a social link"""

    social_name: str
    link: str


class TelegramLinkRequest(BaseModel):
    """Schema for linking Telegram account to current player"""

    tg_id: int = Field(..., description="Telegram user ID")
