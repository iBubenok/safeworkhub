"""Интеграционные тесты уведомлений по событиям проверок."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from app.core.config import get_settings
from app.services.notification_service import NotificationService
from app.services.redis_service import RedisService
from app.tasks.deadline_reminders import scan_due_deadline_reminders


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def register_and_login(client: AsyncClient, email: str):
    payload = {
        "organization_name": "Орг уведомлений",
        "inn": "1653001806",
        "admin_email": email,
        "admin_password": "CheckPass123!",
        "admin_name": "Создатель",
    }
    register = await client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201, register.text
    auth = await client.post("/api/v1/auth/login", json={"email": email, "password": payload["admin_password"]})
    assert auth.status_code == 200, auth.text
    return auth.json(), auth.cookies


async def create_member_and_login(client: AsyncClient, owner_tokens, owner_cookies, email: str):
    created = await client.post(
        "/api/v1/users",
        json={"email": email, "name": "Сотрудник", "password": "MemberPass123!", "role": "member"},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    assert created.status_code == 201, created.text
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "MemberPass123!"})
    assert login.status_code == 200, login.text
    return login.json(), login.cookies, created.json()["id"]


async def create_checklist(client: AsyncClient, tokens, cookies) -> dict:
    payload = {
        "title": "Проверка",
        "status": "published",
        "items": [{"text": "Пункт", "answer_type": "compliance", "required": True}],
    }
    resp = await client.post("/api/v1/checklists", json=payload, headers=auth_headers(tokens), cookies=cookies)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def start_run(client: AsyncClient, tokens, cookies, checklist_id: str, **overrides) -> dict:
    payload = {"checklist_id": checklist_id}
    payload.update(overrides)
    resp = await client.post("/api/v1/checklist-runs", json=payload, headers=auth_headers(tokens), cookies=cookies)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def titles_of(client: AsyncClient, tokens, cookies) -> list[str]:
    resp = await client.get("/api/v1/notifications", headers=auth_headers(tokens), cookies=cookies)
    assert resp.status_code == 200, resp.text
    return [n["title"] for n in resp.json()["items"]]


@pytest.mark.asyncio
async def test_start_notifies_only_assignees(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies, member_id = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"m1_{unique_email}"
    )
    other_tokens, other_cookies, _ = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"m2_{unique_email}"
    )

    run = await start_run(client, owner_tokens, owner_cookies, checklist["id"], assignee_ids=[member_id])
    first_answer = run["answers"][0]["id"]

    assert "Новая проверка" in await titles_of(client, member_tokens, member_cookies)
    # Создатель (инициатор) и посторонний участник — без уведомлений.
    assert await titles_of(client, owner_tokens, owner_cookies) == []
    assert await titles_of(client, other_tokens, other_cookies) == []

    # Завершение уведомляет назначенного, но не инициатора (владельца).
    await client.patch(
        f"/api/v1/checklist-runs/{run['id']}",
        json={"answers": [{"answer_id": first_answer, "value": "compliant"}]},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    done = await client.post(
        f"/api/v1/checklist-runs/{run['id']}/complete", headers=auth_headers(owner_tokens), cookies=owner_cookies
    )
    assert done.status_code == 200, done.text
    assert "Проверка завершена" in await titles_of(client, member_tokens, member_cookies)
    # В тексте уведомления указан завершивший (создатель, имя «Создатель»).
    notifications = await client.get(
        "/api/v1/notifications", headers=auth_headers(member_tokens), cookies=member_cookies
    )
    completed = next(n for n in notifications.json()["items"] if n["title"] == "Проверка завершена")
    assert "Создатель" in completed["message"], completed["message"]
    assert await titles_of(client, owner_tokens, owner_cookies) == []


@pytest.mark.asyncio
async def test_assignee_change_notifications(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, owner_tokens, owner_cookies)
    a_tokens, a_cookies, a_id = await create_member_and_login(client, owner_tokens, owner_cookies, f"a_{unique_email}")
    b_tokens, b_cookies, b_id = await create_member_and_login(client, owner_tokens, owner_cookies, f"b_{unique_email}")

    run = await start_run(client, owner_tokens, owner_cookies, checklist["id"], assignee_ids=[a_id])
    # Меняем состав: убираем A, добавляем B.
    resp = await client.put(
        f"/api/v1/checklist-runs/{run['id']}/assignees",
        json={"assignee_ids": [b_id]},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    assert resp.status_code == 200, resp.text

    assert "Снят доступ к проверке" in await titles_of(client, a_tokens, a_cookies)
    assert "Вас назначили на проверку" in await titles_of(client, b_tokens, b_cookies)


@pytest.mark.asyncio
async def test_deadline_change_notifies_assignee(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies, member_id = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"m_{unique_email}"
    )
    run = await start_run(client, owner_tokens, owner_cookies, checklist["id"], assignee_ids=[member_id])

    future = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    resp = await client.put(
        f"/api/v1/checklist-runs/{run['id']}/deadline",
        json={"due_at": future},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    assert resp.status_code == 200, resp.text
    assert "Изменён срок проверки" in await titles_of(client, member_tokens, member_cookies)


@pytest.mark.asyncio
async def test_deadline_reminder_scan(client: AsyncClient, db_session, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies, member_id = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"m_{unique_email}"
    )
    soon = (datetime.now(UTC) + timedelta(hours=12)).isoformat()
    await start_run(client, owner_tokens, owner_cookies, checklist["id"], assignee_ids=[member_id], due_at=soon)

    redis_client = Redis.from_url(get_settings().redis_url, encoding="utf-8", decode_responses=True)
    notifications = NotificationService(db_session, RedisService(redis_client))
    try:
        processed = await scan_due_deadline_reminders(
            db_session, notifications, threshold_hours=24, now=datetime.now(UTC)
        )
        assert processed == 1
        # Повторный скан — без дублей (флаг deadline_reminded_at выставлен).
        again = await scan_due_deadline_reminders(db_session, notifications, threshold_hours=24, now=datetime.now(UTC))
        assert again == 0
    finally:
        await redis_client.aclose()

    # Напоминание получили и создатель, и назначенный.
    assert "Скоро срок проверки" in await titles_of(client, owner_tokens, owner_cookies)
    assert "Скоро срок проверки" in await titles_of(client, member_tokens, member_cookies)
