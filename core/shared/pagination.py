"""
Pagination utilities for query results
"""

from typing import List, Dict, Any, Optional
from math import ceil


class Paginator:
    """
    Paginator for query results

    Usage:
        query = Model.all()
        paginator = Paginator(query, page=1, per_page=20)
        result = await paginator.get_page()
    """

    def __init__(self, query: Any, page: int = 1, per_page: int = 20):
        """
        Initialize paginator

        Args:
            query: Tortoise ORM query object
            page: Page number (1-based)
            per_page: Items per page
        """
        if page < 1:
            raise ValueError("Page must be >= 1")
        if per_page < 1:
            raise ValueError("Per page must be >= 1")

        self.query = query
        self.page = page
        self.per_page = per_page
        self._total = None

    async def get_total(self) -> int:
        """
        Get total number of items

        Returns:
            Total count
        """
        if self._total is None:
            self._total = await self.query.count()
        return self._total

    async def get_page(self) -> Dict[str, Any]:
        """
        Get current page with metadata

        Returns:
            Dictionary with:
            - items: List of items on current page
            - total: Total number of items
            - page: Current page number
            - per_page: Items per page
            - pages: Total number of pages
            - has_next: Whether there is a next page
            - has_prev: Whether there is a previous page
        """
        total = await self.get_total()
        pages = ceil(total / self.per_page) if total > 0 else 0

        offset = (self.page - 1) * self.per_page
        items = await self.query.offset(offset).limit(self.per_page)

        return {
            "items": items,
            "total": total,
            "page": self.page,
            "per_page": self.per_page,
            "pages": pages,
            "has_next": self.page < pages,
            "has_prev": self.page > 1,
        }

    async def has_next(self) -> bool:
        """
        Check if there is a next page

        Returns:
            True if next page exists
        """
        total = await self.get_total()
        pages = ceil(total / self.per_page) if total > 0 else 0
        return self.page < pages

    async def has_prev(self) -> bool:
        """
        Check if there is a previous page

        Returns:
            True if previous page exists
        """
        return self.page > 1

    async def get_next_page(self) -> Optional[int]:
        """
        Get next page number

        Returns:
            Next page number or None if no next page
        """
        if await self.has_next():
            return self.page + 1
        return None

    async def get_prev_page(self) -> Optional[int]:
        """
        Get previous page number

        Returns:
            Previous page number or None if no previous page
        """
        if await self.has_prev():
            return self.page - 1
        return None
