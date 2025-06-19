import logging

import redis.asyncio as aioredis

from settings import settings

logger = logging.getLogger("sse-server")


class RedisManager:
    """Manages Redis connections."""

    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self._redis = aioredis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            await self._redis.ping()
            logger.info(f"Successfully connected to Redis at {settings.redis_url}")
        except Exception as e:
            logger.critical(f"Failed to connect to Redis: {e}", exc_info=True)
            self._redis = None

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed.")

    def get_client(self) -> aioredis.Redis | None:
        """Get the Redis client."""
        return self._redis


redis_manager = RedisManager()


def get_redis() -> aioredis.Redis | None:
    """Redis dependency for FastAPI routes."""
    return redis_manager.get_client()
