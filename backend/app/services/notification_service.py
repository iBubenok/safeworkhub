from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationSettings
from app.schemas.notification import NotificationCreate, NotificationList, NotificationRead
from app.services.redis_service import RedisService


class NotificationService:
    def __init__(self, db: AsyncSession, redis: RedisService):
        self.db = db
        self.redis = redis

    async def create(self, data: NotificationCreate) -> Notification | None:
        """Создать уведомление и отправить через Redis PubSub."""

        # Проверяем настройки пользователя
        settings = await self._get_settings(data.user_id)
        if settings and data.category not in settings.enabled_categories:
            return None

        notification = Notification(
            user_id=data.user_id,
            title=data.title,
            message=data.message,
            type=data.type,
            category=data.category,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            metadata_=data.metadata,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        # Публикуем в Redis для real-time доставки
        await self.redis.publish_notification(
            user_id=str(data.user_id),
            notification={
                "id": str(notification.id),
                "title": notification.title,
                "message": notification.message,
                "type": notification.type,
                "category": notification.category,
                "created_at": notification.created_at.isoformat(),
            },
        )

        # Обновляем счётчик непрочитанных в Redis
        await self.redis.increment_unread_count(str(data.user_id))

        return notification

    # Массовая рассылка
    async def create_bulk(self, user_ids: list[UUID], data: NotificationCreate) -> list[Notification]:
        """Отправить уведомление нескольким пользователям."""
        notifications: list[Notification] = []
        for user_id in user_ids:
            notification = await self.create(data.model_copy(update={"user_id": user_id}))
            if notification:
                notifications.append(notification)
        return notifications

    # Получение списка уведомлений
    async def get_list(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> NotificationList:
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
        )

        if unread_only:
            query = query.where(Notification.is_read.is_(False))

        query = query.order_by(Notification.created_at.desc())

        # Общее количество
        count_query = select(func.count()).select_from(query.subquery())
        total = int((await self.db.execute(count_query)).scalar() or 0)

        # Непрочитанные
        unread_query = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
            Notification.deleted_at.is_(None),
        )
        unread_count = int((await self.db.execute(unread_query)).scalar() or 0)

        # Пагинация
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return NotificationList(
            items=[NotificationRead.model_validate(item) for item in items],
            unread_count=unread_count,
            total=total,
        )

    async def get_unread_count(self, user_id: UUID) -> int:
        """Получить количество непрочитанных уведомлений из БД."""
        query = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
        )
        return int((await self.db.execute(query)).scalar() or 0)

    # Прочитать одно уведомление
    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        result = cast("CursorResult[Any]", await self.db.execute(stmt))
        await self.db.commit()

        if result.rowcount > 0:
            await self.redis.decrement_unread_count(str(user_id))
            return True
        return False

    # Прочитать все уведомления
    async def mark_all_as_read(self, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        result = cast("CursorResult[Any]", await self.db.execute(stmt))
        await self.db.commit()

        await self.redis.reset_unread_count(str(user_id))

        return int(result.rowcount or 0)

    # Удалить уведомление (мягко: проставляем deleted_at, строку не убираем из БД)
    async def delete(self, notification_id: UUID, user_id: UUID) -> bool:
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.utcnow())
            .returning(Notification.is_read)
        )
        result = cast("CursorResult[Any]", await self.db.execute(stmt))
        row = result.first()
        await self.db.commit()

        if row is None:
            return False
        # Если удаляем непрочитанное — синхронно уменьшаем счётчик в Redis.
        if not row[0]:
            await self.redis.decrement_unread_count(str(user_id))
        return True

    # Удалить выбранные уведомления (мягко)
    async def delete_many(self, notification_ids: list[UUID], user_id: UUID) -> int:
        if not notification_ids:
            return 0
        stmt = (
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.utcnow())
            .returning(Notification.is_read)
        )
        result = cast("CursorResult[Any]", await self.db.execute(stmt))
        rows = result.all()
        await self.db.commit()

        unread_deleted = sum(1 for row in rows if not row[0])
        for _ in range(unread_deleted):
            await self.redis.decrement_unread_count(str(user_id))
        return len(rows)

    # Удалить все уведомления пользователя (мягко)
    async def delete_all(self, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.utcnow())
        )
        result = cast("CursorResult[Any]", await self.db.execute(stmt))
        await self.db.commit()

        await self.redis.reset_unread_count(str(user_id))
        return int(result.rowcount or 0)

    # Настройки пользователя для уведомлений
    async def _get_settings(self, user_id: UUID) -> NotificationSettings | None:
        query = select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
