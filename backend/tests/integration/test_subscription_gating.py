"""Интеграционные тесты гейтинга по подписке.

Правило: чтение платных модулей свободно, запись гейтится подпиской. При истёкшей
подписке запись возвращает 403 с кодом SUBSCRIPTION_INACTIVE (чтобы клиент показал
призыв продлить), а чтение продолжает работать.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription, SubscriptionStatus


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def register_and_login(client: AsyncClient, email: str):
    payload = {
        "organization_name": "Орг подписки",
        "inn": "1653001806",
        "admin_email": email,
        "admin_password": "CheckPass123!",
        "admin_name": "Владелец",
    }
    register = await client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201, register.text
    auth = await client.post("/api/v1/auth/login", json={"email": email, "password": payload["admin_password"]})
    assert auth.status_code == 200, auth.text
    return auth.json(), auth.cookies


async def expire_subscription(db_session: AsyncSession, organization_id: int) -> None:
    await db_session.execute(
        update(Subscription)
        .where(Subscription.organization_id == organization_id)
        .values(status=SubscriptionStatus.EXPIRED)
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_trial_can_write(client: AsyncClient, unique_email: str):
    """На триале (по умолчанию) запись разрешена."""
    tokens, cookies = await register_and_login(client, unique_email)
    art = await client.post(
        "/api/v1/materials/articles",
        json={"title": "Черновик", "content": "текст", "status": "draft"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert art.status_code == 201, art.text


@pytest.mark.asyncio
async def test_expired_reads_ok_writes_blocked_materials(client: AsyncClient, db_session, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    org_id = tokens["organization_id"]
    created = await client.post(
        "/api/v1/materials/articles",
        json={"title": "Правила по ОТ", "content": "текст", "status": "published"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    material_id = created.json()["id"]

    await expire_subscription(db_session, org_id)

    # Чтение работает даже при истёкшей подписке.
    lst = await client.get("/api/v1/materials", headers=auth_headers(tokens), cookies=cookies)
    assert lst.status_code == 200, lst.text
    detail = await client.get(f"/api/v1/materials/{material_id}", headers=auth_headers(tokens), cookies=cookies)
    assert detail.status_code == 200, detail.text

    # Запись блокируется с распознаваемым кодом.
    write = await client.post(
        "/api/v1/materials/articles",
        json={"title": "Новая", "content": "x", "status": "draft"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert write.status_code == 403, write.text
    assert write.json()["error"]["code"] == "SUBSCRIPTION_INACTIVE"


@pytest.mark.asyncio
async def test_expired_reads_ok_writes_blocked_checklists_and_runs(client: AsyncClient, db_session, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    org_id = tokens["organization_id"]
    checklist = await client.post(
        "/api/v1/checklists",
        json={"title": "Чек-лист", "status": "published", "items": [{"text": "П1", "answer_type": "compliance"}]},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert checklist.status_code == 201, checklist.text
    checklist_id = checklist.json()["id"]

    await expire_subscription(db_session, org_id)

    # Чтение чек-листов работает.
    lst = await client.get("/api/v1/checklists", headers=auth_headers(tokens), cookies=cookies)
    assert lst.status_code == 200, lst.text

    # Проведение проверки — запись, блокируется.
    run = await client.post(
        "/api/v1/checklist-runs",
        json={"checklist_id": checklist_id},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert run.status_code == 403, run.text
    assert run.json()["error"]["code"] == "SUBSCRIPTION_INACTIVE"

    # Создание чек-листа — запись, блокируется.
    create = await client.post(
        "/api/v1/checklists",
        json={"title": "Ещё один", "items": []},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert create.status_code == 403, create.text
    assert create.json()["error"]["code"] == "SUBSCRIPTION_INACTIVE"
