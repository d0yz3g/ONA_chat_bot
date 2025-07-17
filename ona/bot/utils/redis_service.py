import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisRateLimiter:
    def __init__(self):
        self.redis = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            encoding="utf-8"
        )

    async def is_allowed(self, user_id: int, limit: int = 2, window: int = 10) -> bool:
        """
        Ограничивает пользователя: limit сообщений за window секунд.
        """
        try:
            await self.redis.ping()  # Проверяем, что Redis жив

            key = f"rate_limit:{user_id}"
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window)

            print(f"[RedisLimiter] user_id={user_id}, current={current}, allowed={current <= limit}")
            return current <= limit
        except Exception as e:
            print(f"[RedisLimiter] Ошибка подключения: {e}")
            return True  # В случае ошибки разрешаем, чтобы не блокировать
