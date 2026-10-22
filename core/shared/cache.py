"""
Simple in-memory cache implementation
"""

import time
from typing import Any, Optional, Dict
from datetime import timedelta
from threading import Lock
from core.shared.logger import logger


class Cache:
    """
    Simple in-memory cache with TTL support

    Thread-safe cache implementation for frequently accessed data.
    """

    def __init__(self):
        """Initialize cache"""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if entry["expires_at"] is not None and time.time() > entry["expires_at"]:
                # Expired, remove it
                del self._cache[key]
                return None

            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (optional, None = no expiration)
        """
        with self._lock:
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl.total_seconds()

            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time(),
            }

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries

        Args:
            pattern: Pattern to match keys (if None, invalidates all)

        Returns:
            Number of invalidated entries
        """
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info("🗑️ Cache cleared", count=count)
                return count

            # Simple pattern matching (contains)
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]

            logger.info(
                "🗑️ Cache invalidated", pattern=pattern, count=len(keys_to_remove)
            )
            return len(keys_to_remove)

    def clear(self) -> None:
        """
        Clear all cache entries
        """
        with self._lock:
            self._cache.clear()
            logger.info("🗑️ Cache cleared")

    def size(self) -> int:
        """
        Get cache size

        Returns:
            Number of entries in cache
        """
        with self._lock:
            # Remove expired entries first
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry["expires_at"] is not None and time.time() > entry["expires_at"]
            ]
            for key in expired_keys:
                del self._cache[key]

            return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            # Remove expired entries first
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry["expires_at"] is not None and time.time() > entry["expires_at"]
            ]
            for key in expired_keys:
                del self._cache[key]

            return {
                "size": len(self._cache),
                "keys": list(self._cache.keys()),
            }


# Global cache instance
cache = Cache()
