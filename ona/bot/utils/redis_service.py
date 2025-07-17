import redis.asyncio as redis  # ✅ Новый корректный импорт
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

class RedisRateLimiter:
    def __init__(self):
        self.redis = None

    async def connect(self):
        if not self.redis:
            self.redis = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True,
                encoding="utf-8"
            )

    async def is_allowed(self, user_id: int, limit: int = 5, window: int = 10) -> bool:
        """
        Ограничивает пользователя: limit сообщений за window секунд.
        """
        await self.connect()
        key = f"rate_limit:{user_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window)
        return current <= limit
