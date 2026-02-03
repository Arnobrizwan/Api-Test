"""Caching utilities for OCR results.

This module provides a thread-safe, TTL-based cache for storing
OCR results to improve performance for repeated requests.
"""

import threading
from typing import Optional, Any, Dict

from cachetools import TTLCache

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class OCRCache:
    """Thread-safe cache for OCR results using TTL eviction.

    Implements a singleton pattern to ensure a single cache instance
    across the application. Uses SHA256 hashes of image content as keys.

    Attributes:
        _cache: The underlying TTLCache instance
        _lock: Threading lock for thread-safe operations
        _hits: Counter for cache hits
        _misses: Counter for cache misses
    """

    _instance: Optional["OCRCache"] = None
    _creation_lock = threading.Lock()

    def __new__(cls) -> "OCRCache":
        """Create or return the singleton instance.

        Returns:
            The singleton OCRCache instance
        """
        if cls._instance is None:
            with cls._creation_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the cache if not already initialized."""
        if self._initialized:
            return

        self._cache: TTLCache = TTLCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl_seconds
        )
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._initialized = True

        logger.info(
            f"OCR Cache initialized",
            extra={
                "max_size": settings.cache_max_size,
                "ttl_seconds": settings.cache_ttl_seconds,
            }
        )

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve an item from the cache.

        Args:
            key: The cache key (typically SHA256 hash of image)

        Returns:
            The cached value if found, None otherwise
        """
        with self._lock:
            result = self._cache.get(key)

            if result is not None:
                self._hits += 1
                logger.debug(f"Cache hit: key={key[:16]}...")
            else:
                self._misses += 1
                logger.debug(f"Cache miss: key={key[:16]}...")

            return result

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Store an item in the cache.

        Args:
            key: The cache key
            value: The value to cache (must be serializable)
        """
        with self._lock:
            self._cache[key] = value
            logger.debug(f"Cache set: key={key[:16]}...")

    def delete(self, key: str) -> bool:
        """Remove an item from the cache.

        Args:
            key: The cache key to remove

        Returns:
            True if the key was found and removed, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache delete: key={key[:16]}...")
                return True
            return False

    def clear(self) -> None:
        """Remove all items from the cache."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary containing cache metrics:
            - size: Current number of cached items
            - max_size: Maximum cache size
            - ttl_seconds: Time-to-live for cache entries
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate_percent: Cache hit rate as percentage
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": settings.cache_max_size,
                "ttl_seconds": settings.cache_ttl_seconds,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
            }

    def __len__(self) -> int:
        """Return the current number of cached items."""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        with self._lock:
            return key in self._cache


# Global cache instance
ocr_cache = OCRCache()
