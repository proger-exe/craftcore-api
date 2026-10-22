"""
Voting request/response schemas
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class VoteOptionCreate(BaseModel):
    id: Optional[int] = None
    text: str


class VoteCreate(BaseModel):
    title: str
    description: str = ""
    options: List[VoteOptionCreate]
    ends_at: Optional[datetime] = None


class VoteOptionResponse(BaseModel):
    id: int
    text: str
    votes: int
    percentage: Optional[float] = None


class VoteResponse(BaseModel):
    id: int
    created_by_id: Optional[int] = None
    title: str
    description: str
    options: List[VoteOptionResponse]
    total_votes: Optional[int] = None
    created_at: datetime
    ends_at: Optional[datetime] = None


class VoteCastRequest(BaseModel):
    option_id: int


class VoteStatsResponse(BaseModel):
    total_votes: int
    options: List[VoteOptionResponse]
