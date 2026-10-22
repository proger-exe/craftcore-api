"""Player-created quest marketplace schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlayerQuestCreate(BaseModel):
    title: str
    description: str
    reward: int


class PlayerQuestApplicationCreate(BaseModel):
    cover_letter: Optional[str] = None


class PlayerQuestSubmissionRequest(BaseModel):
    submission_message: Optional[str] = None


class PlayerQuestReviewRequest(BaseModel):
    comment: Optional[str] = None


class PlayerQuestResponse(BaseModel):
    id: int
    creator_id: int
    title: str
    description: str
    reward: int
    status: str
    executor_id: Optional[int] = None
    applications_count: int
    my_application_status: Optional[str] = None
    submission_message: Optional[str] = None
    review_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    can_apply: bool
    can_view_applications: bool
    can_cancel: bool
    can_delete: bool
    can_submit: bool
    can_approve: bool
    can_request_changes: bool
    can_abandon: bool


class PlayerQuestApplicationResponse(BaseModel):
    id: int
    quest_id: int
    applicant_id: int
    status: str
    cover_letter: Optional[str] = None
    submission_message: Optional[str] = None
    review_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    quest_title: Optional[str] = None
