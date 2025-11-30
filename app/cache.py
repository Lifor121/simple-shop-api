import os
import redis.asyncio as redis
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def get_redis_client() -> Redis:
    """
    Provides an asynchronous Redis client.
    """
    return redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

# Optional: A global client instance if you prefer to manage the connection globally.
# However, using a dependency injection approach with get_redis_client is often cleaner in FastAPI.
# redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
