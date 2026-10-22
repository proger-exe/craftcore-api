"""Nick change request schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class NickChangeRequestCreate(BaseModel):
    new_nick: str


class NickChangeRequestResponse(BaseModel):
    id: int
    player_id: int
    new_nick: str
    status: str
    created_at: datetime
