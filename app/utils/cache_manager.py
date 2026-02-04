"""Cache manager for selecting between in-memory and Redis cache."""

import json
from typing import Any, Optional
from cachetools import TTLCache
import redis

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

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
    def __init__(self, maxsize: int, ttl: int):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Any:
        return self.cache.get(key)

    def set(self, key: str, value: Any):
        self.cache[key] = value

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
    def __init__(self, host: str, port: int, db: int, ttl: int, password: Optional[str] = None):
        try:
            # Added ssl=True and ssl_cert_reqs=None to support public cloud Redis (like Upstash/Redis Cloud)
            # which usually require TLS/SSL.
            self.redis = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                password=password, 
                decode_responses=True,
                ssl=True,
                ssl_cert_reqs="required"
            )
            self.redis.ping()
            self.ttl = ttl
            logger.info(f"Redis cache connected successfully to {host}:{port}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}. Caching will be disabled.")
            self.redis = None

    def get(self, key: str) -> Any:
        if not self.redis:
            return None
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            return None

    def set(self, key: str, value: Any):
        if not self.redis:
            return
        try:
            # Ensure value is JSON serializable (handling Pydantic objects)
            # We use a custom encoder or convert to dict in the service, 
            # but this is a safety net.
            self.redis.setex(key, self.ttl, json.dumps(value, default=str))
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
        if self.redis:
            self.redis.flushdb()


def get_cache() -> CacheInterface:
    if settings.cache_type == "redis" and settings.enable_cache:
        return RedisCache(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            ttl=settings.cache_ttl_seconds,
            password=settings.redis_password,
        )
    return InMemoryCache(
        maxsize=settings.cache_max_size,
        ttl=settings.cache_ttl_seconds
    )

ocr_cache = get_cache()