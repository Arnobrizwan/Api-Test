"""Cache manager for selecting between in-memory and Redis cache."""

import json
import re
from typing import Any, Optional

from cachetools import TTLCache
import redis

from ..core.config import settings
from ..core.constants import CACHE_NAMESPACE, REDIS_SCAN_COUNT, CACHE_KEY_LENGTH
from ..core.logging import get_logger

logger = get_logger(__name__)

# Cache key validation pattern (SHA256 hex string)
CACHE_KEY_PATTERN = re.compile(r'^[a-f0-9]{' + str(CACHE_KEY_LENGTH) + '}$')


def validate_cache_key(key: str) -> bool:
    """Validate cache key format (must be SHA256 hex string).
    
    Args:
        key: Cache key to validate
        
    Returns:
        True if key is valid
    """
    if not key:
        return False
    return bool(CACHE_KEY_PATTERN.match(key))

class CacheInterface:
    def get(self, key: str) -> Any:
        raise NotImplementedError

    def set(self, key: str, value: Any):
        raise NotImplementedError

    def get_stats(self) -> dict:
        return {}
    
    def clear(self):
        raise NotImplementedError

class InMemoryCache(CacheInterface):
    def __init__(self, maxsize: int, ttl: int, namespace: str = CACHE_NAMESPACE):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.namespace = namespace

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"{self.namespace}{key}"

    def get(self, key: str) -> Any:
        if not validate_cache_key(key):
            logger.warning(f"Invalid cache key format: {key[:16]}...")
            return None
        return self.cache.get(self._make_key(key))

    def set(self, key: str, value: Any):
        if not validate_cache_key(key):
            logger.warning(f"Invalid cache key format: {key[:16]}...")
            return
        self.cache[self._make_key(key)] = value

    def get_stats(self) -> dict:
        return {
            "type": "in-memory",
            "max_size": self.cache.maxsize,
            "ttl": self.cache.ttl,
            "current_size": self.cache.currsize,
        }

    def clear(self):
        self.cache.clear()

class RedisCache(CacheInterface):
    def __init__(self, host: str, port: int, db: int, ttl: int, password: Optional[str] = None,
                 namespace: str = CACHE_NAMESPACE, use_ssl: bool = False):
        self.namespace = namespace
        self.ttl = ttl
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._use_ssl = use_ssl
        self.redis = None
        self._connect()

    def _connect(self) -> bool:
        """Attempt to connect to Redis. Returns True if successful."""
        try:
            connection_kwargs = {
                "host": self._host,
                "port": self._port,
                "db": self._db,
                "password": self._password,
                "decode_responses": True,
            }
            # Only enable SSL if configured (for cloud Redis like Upstash/Redis Cloud)
            if self._use_ssl:
                connection_kwargs["ssl"] = True
                connection_kwargs["ssl_cert_reqs"] = "required"

            self.redis = redis.Redis(**connection_kwargs)
            self.redis.ping()
            logger.info(f"Redis cache connected successfully to {self._host}:{self._port}")
            return True
        except redis.exceptions.ConnectionError as e:
            if settings.redis_required:
                logger.critical(f"Redis connection failed and REDIS_REQUIRED is set: {e}")
                raise RuntimeError(f"Redis connection failed: {e}") from e
            logger.error(f"Redis connection failed: {e}. Caching will use in-memory fallback.")
            self.redis = None
            return False

    def _ensure_connected(self) -> bool:
        """Ensure Redis is connected, attempt reconnection if not."""
        if self.redis:
            try:
                self.redis.ping()
                return True
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError,
                    redis.exceptions.ResponseError) as e:
                logger.warning(f"Redis connection issue ({type(e).__name__}), attempting reconnection...")
                self.redis = None
        return self._connect()

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"{self.namespace}{key}"

    def get(self, key: str) -> Any:
        if not validate_cache_key(key):
            logger.warning(f"Invalid cache key format: {key[:16]}...")
            return None
        if not self._ensure_connected():
            return None
        try:
            value = self.redis.get(self._make_key(key))
            return json.loads(value) if value else None
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            logger.warning(f"Redis get failed ({type(e).__name__}): connection issue")
            self.redis = None
            return None
        except redis.exceptions.ResponseError as e:
            logger.warning(f"Redis get failed (ResponseError): {e}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Redis get failed: invalid JSON in cache - {e}")
            return None
        except Exception as e:
            logger.warning(f"Redis get failed ({type(e).__name__}): {e}")
            return None

    def set(self, key: str, value: Any):
        if not validate_cache_key(key):
            logger.warning(f"Invalid cache key format: {key[:16]}...")
            return
        if not self._ensure_connected():
            return
        try:
            # Ensure value is JSON serializable (handling Pydantic objects)
            self.redis.setex(self._make_key(key), self.ttl, json.dumps(value, default=str))
        except redis.exceptions.ConnectionError:
            logger.warning("Redis set failed: connection lost")
            self.redis = None
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")

    def get_stats(self) -> dict:
        if not self.redis:
            return {"type": "redis", "status": "disconnected"}
        try:
            info = self.redis.info()
            return {
                "type": "redis",
                "status": "connected",
                "ttl": self.ttl,
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else self.redis.dbsize(),
            }
        except Exception as e:
            return {"type": "redis", "status": "error", "error": str(e)}
    
    def clear(self):
        """Clear only namespaced keys (not entire database)."""
        if not self._ensure_connected():
            return
        try:
            # Use SCAN to find keys with our namespace prefix and delete them
            # This is safer than flushdb() which would delete ALL keys in the database
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = self.redis.scan(
                    cursor, match=f"{self.namespace}*", count=REDIS_SCAN_COUNT
                )
                if keys:
                    self.redis.delete(*keys)
                    deleted_count += len(keys)
                if cursor == 0:
                    break
            logger.info(f"Cleared {deleted_count} cached keys with namespace '{self.namespace}'")
        except Exception as e:
            logger.warning(f"Redis clear failed: {e}")


def get_cache() -> CacheInterface:
    """Get cache instance based on configuration.
    
    Creates a new cache instance each time - use this function
    instead of module-level globals for proper lifespan management.
    """
    if settings.cache_type == "redis" and settings.enable_cache:
        redis_cache = RedisCache(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            ttl=settings.cache_ttl_seconds,
            password=settings.redis_password,
            use_ssl=settings.redis_ssl,
        )
        # If Redis failed but is required, let it fail
        # Otherwise return it (even if disconnected, it will fallback)
        return redis_cache
    return InMemoryCache(
        maxsize=settings.cache_max_size,
        ttl=settings.cache_ttl_seconds
    )