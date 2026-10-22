"""
Admin-only request/response schemas (dashboard, search, settings, etc.)
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class PlayerSearchResult(BaseModel):
    """Short player card for admin search results."""

    player_id: int
    tg_id: Optional[int] = None
    nickname: Optional[str] = None
    role: str


class BotSettingsResponse(BaseModel):
    """All bot settings as key-value."""

    settings: Dict[str, str] = {}


class BotSettingsUpdate(BaseModel):
    """Update bot settings (partial)."""

    settings: Dict[str, str] = {}


class RankingBalanceEntry(BaseModel):
    player_id: int
    nickname: Optional[str] = None
    balance: int
    rank: int


class RankingOnlineTimeEntry(BaseModel):
    player_id: int
    nickname: Optional[str] = None
    total_online_time: int
    rank: int


class WalletFreezeRequest(BaseModel):
    amount: int
    reason: str = ""


class WalletUnfreezeRequest(BaseModel):
    amount: int


class PlayerSessionCreate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
