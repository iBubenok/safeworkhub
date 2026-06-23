from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from redis.exceptions import RedisError

from app.models.notification import Notification, NotificationSettings
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService
from app.services.redis_service import RedisService


class _FakeScalarResult:
    def __init__(self, value: object | None = None, items: Iterable[object] | None = None) -> None:
        self._value = value
        self._items = list(items or [])

    def scalar_one_or_none(self) -> object | None:
        return self._value

    def scalar(self) -> object | None:
        return self._value

    def scalars(self) -> _FakeScalarResult:
        return self

    def all(self) -> list[object]:
        return self._items

    def first(self) -> object | None:
        return self._items[0] if self._items else self._value


class _FakeRedisClient:
    def __init__(self) -> None:
        self.publish = AsyncMock()
        self.get = AsyncMock(return_value=None)
        self.incr = AsyncMock()
        self.decr = AsyncMock()
        self.set = AsyncMock()


@pytest.fixture
def notification_service() -> tuple[NotificationService, SimpleNamespace, _FakeRedisClient]:
    db = SimpleNamespace(
        add=MagicMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
        execute=AsyncMock(),
    )
    redis_client = _FakeRedisClient()
    service = NotificationService(db, RedisService(redis_client))
    return service, db, redis_client


def _notification(
    *,
    user_id: UUID,
    title: str = "Test",
    message: str = "Message",
    is_read: bool = False,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type="info",
        category="system",
        entity_type=None,
        entity_id=None,
        is_read=is_read,
        read_at=None,
        metadata_={"source": "test"},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    notification.id = uuid4()
    return notification


@pytest.mark.asyncio
async def test_create_notification_persists_and_publishes(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, redis_client = notification_service
    user_id = uuid4()
    data = NotificationCreate(
        user_id=user_id,
        title="Created",
        message="Created message",
        category="system",
        metadata={"source": "unit"},
    )
    db.execute.return_value = _FakeScalarResult(None)
    db.refresh.side_effect = lambda notification: setattr(
        notification,
        "created_at",
        datetime(2026, 1, 1, tzinfo=UTC),
    )

    notification = await service.create(data)

    assert notification is not None
    assert notification.user_id == user_id
    assert db.add.called
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
    redis_client.publish.assert_awaited_once()
    redis_client.incr.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_notification_respects_disabled_category(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, redis_client = notification_service
    user_id = uuid4()
    disabled = NotificationSettings(
        user_id=user_id,
        enabled_categories=["task"],
        in_app=True,
        email=False,
    )
    data = NotificationCreate(
        user_id=user_id,
        title="Blocked",
        message="Blocked message",
        category="system",
    )
    db.execute.return_value = _FakeScalarResult(disabled)

    notification = await service.create(data)

    assert notification is None
    db.add.assert_not_called()
    db.commit.assert_not_called()
    redis_client.publish.assert_not_called()
    redis_client.incr.assert_not_called()


@pytest.mark.asyncio
async def test_get_list_returns_counts_and_serialized_items(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, _ = notification_service
    user_id = uuid4()
    first = _notification(user_id=user_id, title="First")
    second = _notification(user_id=user_id, title="Second", is_read=True)

    db.execute.side_effect = [
        _FakeScalarResult(2),
        _FakeScalarResult(1),
        _FakeScalarResult(items=[first, second]),
    ]

    result = await service.get_list(user_id, limit=10, offset=0, unread_only=False)

    assert result.total == 2
    assert result.unread_count == 1
    assert [item.title for item in result.items] == ["First", "Second"]


@pytest.mark.asyncio
async def test_get_unread_count_reads_from_database(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, _ = notification_service
    db.execute.return_value = _FakeScalarResult(5)

    unread_count = await service.get_unread_count(uuid4())

    assert unread_count == 5


@pytest.mark.asyncio
async def test_mark_as_read_updates_database_and_redis(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, redis_client = notification_service
    db.execute.return_value = SimpleNamespace(rowcount=1)
    redis_client.get.return_value = "1"

    success = await service.mark_as_read(uuid4(), uuid4())

    assert success is True
    db.commit.assert_awaited_once()
    redis_client.get.assert_awaited_once()
    redis_client.decr.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_all_as_read_updates_all_rows(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, redis_client = notification_service
    db.execute.return_value = SimpleNamespace(rowcount=3)

    marked = await service.mark_all_as_read(uuid4())

    assert marked == 3
    db.commit.assert_awaited_once()
    redis_client.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_notification_soft_deletes_and_decrements_unread(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, redis_client = notification_service
    # RETURNING is_read = False -> уведомление было непрочитанным
    db.execute.return_value = _FakeScalarResult(items=[(False,)])
    redis_client.get.return_value = "1"

    deleted = await service.delete(uuid4(), uuid4())

    assert deleted is True
    db.commit.assert_awaited_once()
    redis_client.decr.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_notification_returns_false_when_missing(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, redis_client = notification_service
    db.execute.return_value = _FakeScalarResult(items=[])

    deleted = await service.delete(uuid4(), uuid4())

    assert deleted is False
    redis_client.decr.assert_not_called()


@pytest.mark.asyncio
async def test_delete_many_counts_rows_and_decrements_unread(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, redis_client = notification_service
    # Два удалённых: одно непрочитанное (False), одно прочитанное (True)
    db.execute.return_value = _FakeScalarResult(items=[(False,), (True,)])
    redis_client.get.return_value = "5"

    deleted = await service.delete_many([uuid4(), uuid4()], uuid4())

    assert deleted == 2
    db.commit.assert_awaited_once()
    redis_client.decr.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_many_empty_list_is_noop(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, _ = notification_service

    deleted = await service.delete_many([], uuid4())

    assert deleted == 0
    db.execute.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_all_resets_unread_count(
    notification_service: tuple[NotificationService, SimpleNamespace, _FakeRedisClient],
) -> None:
    service, db, redis_client = notification_service
    db.execute.return_value = SimpleNamespace(rowcount=4)

    deleted = await service.delete_all(uuid4())

    assert deleted == 4
    db.commit.assert_awaited_once()
    redis_client.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_service_swallow_backend_errors() -> None:
    redis_client = _FakeRedisClient()
    redis_client.publish.side_effect = RedisError("boom")
    redis_client.get.side_effect = RedisError("boom")
    redis_client.incr.side_effect = RedisError("boom")
    redis_client.decr.side_effect = RedisError("boom")
    redis_client.set.side_effect = RedisError("boom")
    service = RedisService(redis_client)

    await service.publish_notification("user", {"id": "1"})
    assert await service.get_unread_count("user") == 0
    await service.increment_unread_count("user")
    await service.decrement_unread_count("user")
    await service.reset_unread_count("user")
