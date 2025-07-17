import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")  # Railway передаёт именно так

class RedisRateLimiter:
    def __init__(self):
        self.redis = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            encoding="utf-8"
        )

    async def is_allowed(self, user_id: int, limit: int = 5, window: int = 10) -> bool:
        """
        Ограничивает пользователя: limit сообщений за window секунд.
        """
        key = f"rate_limit:{user_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window)
        return current <= limit
