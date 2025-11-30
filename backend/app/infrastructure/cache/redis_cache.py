"""Redis cache service for caching frequently accessed data."""
import json
from typing import Optional, Any
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache client wrapper."""

    _client: Optional[Any] = None

    @classmethod
    async def get_client(cls):
        """Get or create Redis client."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis async support not available. Install redis[hiredis]")

        if cls._client is None:
            try:
                redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
                cls._client = redis.from_url(redis_url, decode_responses=True)
                await cls._client.ping()
                logger.info("Connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return cls._client

    @classmethod
    async def close(cls):
        """Close Redis connection."""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("Closed Redis connection")

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not REDIS_AVAILABLE:
            return None
        try:
            client = await cls.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    @classmethod
    async def set(cls, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL."""
        if not REDIS_AVAILABLE:
            return
        try:
            client = await cls.get_client()
            serialized = json.dumps(value, default=str)
            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")

    @classmethod
    async def delete(cls, key: str):
        """Delete key from cache."""
        if not REDIS_AVAILABLE:
            return
        try:
            client = await cls.get_client()
            await client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")

    @classmethod
    async def exists(cls, key: str) -> bool:
        """Check if key exists."""
        if not REDIS_AVAILABLE:
            return False
        try:
            client = await cls.get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

cache = RedisCache()
