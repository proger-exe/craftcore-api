"""
Identity schemas for TG <-> nick lookup (admin/moderator)
"""

from typing import Optional
from pydantic import BaseModel


class IdentityResponse(BaseModel):
    """Response for identity lookup by nick or tg_id."""

    player_id: Optional[int] = None
    tg_id: Optional[int] = None
    nick: Optional[str] = None
    verified: bool = False
