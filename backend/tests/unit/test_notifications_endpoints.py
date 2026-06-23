from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.endpoints.notifications import (
    delete_all_notifications,
    delete_notification,
    delete_selected,
    get_notifications,
    get_unread_count,
    mark_all_as_read,
    mark_as_read,
)
from app.api.v1.endpoints.notifications_sse import notification_stream
from app.schemas.notification import NotificationDeleteRequest


@pytest.mark.asyncio
async def test_notification_endpoints_delegate_to_service() -> None:
    ctx = SimpleNamespace(user=SimpleNamespace(id=uuid4()))
    service = SimpleNamespace(
        get_list=AsyncMock(return_value=SimpleNamespace(items=[], unread_count=0, total=0)),
        get_unread_count=AsyncMock(return_value=4),
        mark_as_read=AsyncMock(return_value=True),
        mark_all_as_read=AsyncMock(return_value=2),
        delete=AsyncMock(return_value=True),
        delete_many=AsyncMock(return_value=3),
        delete_all=AsyncMock(return_value=5),
    )

    list_result = await get_notifications(ctx, service, limit=10, offset=0, unread_only=False)
    unread_result = await get_unread_count(ctx, service)
    read_result = await mark_as_read(uuid4(), ctx, service)
    all_result = await mark_all_as_read(ctx, service)
    delete_result = await delete_notification(uuid4(), ctx, service)
    selected_result = await delete_selected(NotificationDeleteRequest(ids=[uuid4(), uuid4()]), ctx, service)
    delete_all_result = await delete_all_notifications(ctx, service)

    assert list_result.total == 0
    assert unread_result == {"unread_count": 4}
    assert read_result == {"success": True}
    assert all_result == {"marked_count": 2}
    assert delete_result == {"success": True}
    assert selected_result == {"deleted_count": 3}
    assert delete_all_result == {"deleted_count": 5}


@pytest.mark.asyncio
async def test_notification_stream_yields_message_and_heartbeat() -> None:
    ctx = SimpleNamespace(user=SimpleNamespace(id=uuid4()))

    class _FakePubSub:
        def __init__(self) -> None:
            self.subscribed: list[str] = []
            self.unsubscribed: list[str] = []
            self.closed = False
            self.calls = 0

        async def subscribe(self, channel: str) -> None:
            self.subscribed.append(channel)

        async def get_message(
            self,
            *,
            ignore_subscribe_messages: bool,
            timeout: float,
        ) -> dict[str, str] | None:
            _ = ignore_subscribe_messages
            _ = timeout
            self.calls += 1
            if self.calls == 1:
                return {"type": "message", "data": '{"id":"1"}'}
            return None

        async def unsubscribe(self, channel: str) -> None:
            self.unsubscribed.append(channel)

        async def close(self) -> None:
            self.closed = True

    class _FakeRedisClient:
        def __init__(self) -> None:
            self.pubsub_instance = _FakePubSub()

        def pubsub(self) -> _FakePubSub:
            return self.pubsub_instance

    response = await notification_stream(ctx, _FakeRedisClient())
    iterator = response.body_iterator

    first = await iterator.__anext__()
    second = await iterator.__anext__()
    await iterator.aclose()

    assert "data:" in first
    assert ": heartbeat" in second
