import json
import logging

import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    # Публикация уведомлений
    async def publish_notification(self, user_id: str, notification: dict):
        """Публикуем уведомление в канал пользователя."""
        channel = f"notifications:{user_id}"
        try:
            await self.redis.publish(channel, json.dumps(notification))
        except RedisError:
            logger.warning(
                "Redis publish failed for notifications channel",
                extra={"user_id": user_id, "channel": channel},
            )

    # Счётчик непрочитанных уведомлений
    async def get_unread_count(self, user_id: str) -> int:
        try:
            count = await self.redis.get(f"unread_count:{user_id}")
            return int(count) if count else 0
        except RedisError:
            logger.warning(
                "Redis unread count read failed",
                extra={"user_id": user_id},
            )
            return 0

    async def increment_unread_count(self, user_id: str):
        try:
            await self.redis.incr(f"unread_count:{user_id}")
        except RedisError:
            logger.warning(
                "Redis unread count increment failed",
                extra={"user_id": user_id},
            )

    async def decrement_unread_count(self, user_id: str):
        try:
            count = await self.get_unread_count(user_id)
            if count > 0:
                await self.redis.decr(f"unread_count:{user_id}")
        except RedisError:
            logger.warning(
                "Redis unread count decrement failed",
                extra={"user_id": user_id},
            )

    async def reset_unread_count(self, user_id: str):
        try:
            await self.redis.set(f"unread_count:{user_id}", 0)
        except RedisError:
            logger.warning(
                "Redis unread count reset failed",
                extra={"user_id": user_id},
            )
