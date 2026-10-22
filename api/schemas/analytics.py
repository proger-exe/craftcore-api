from datetime import datetime
from typing import List

from pydantic import BaseModel


class PlaytimeRewardEntry(BaseModel):
    player_id: int
    playtime_seconds: int


class PlaytimeRewardBatch(BaseModel):
    players: List[PlaytimeRewardEntry]


class PlaytimeRewardRecord(BaseModel):
    id: int
    player_id: int
    playtime_seconds: int
    created_at: datetime
