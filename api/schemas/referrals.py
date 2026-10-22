"""Referral request/response schemas."""

from typing import List, Optional
from pydantic import BaseModel


class ReferralCodeResponse(BaseModel):
    code: str
    referrals_count: int = 0


class ReferralJoinRequest(BaseModel):
    code: str


class ReferralStatsResponse(BaseModel):
    code: str
    total_referrals: int
    qualified: int
    rewards: List[dict] = []
