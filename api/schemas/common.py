"""
Common schemas for API
"""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Standard success response"""

    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""

    success: bool = False
    error: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""

    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginationParams(BaseModel):
    """Pagination parameters"""

    page: int = 1
    per_page: int = 20

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "per_page": 20,
            }
        }
