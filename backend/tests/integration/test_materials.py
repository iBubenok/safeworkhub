"""Интеграционные тесты для базы знаний и ограничений подписки."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import Subscription, SubscriptionStatus


def build_registration_payload(email: str) -> dict:
    return {
        "organization_name": "Организация материалов",
        "inn": "1653001806",
        "admin_email": email,
        "admin_password": "MaterialPass123!",
        "admin_name": "Материаловед",
    }


async def register_and_login(client: AsyncClient, email: str):
    payload = build_registration_payload(email)
    register = await client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201
    auth = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["admin_email"], "password": payload["admin_password"]},
    )
    assert auth.status_code == 200
    tokens = auth.json()
    return tokens, auth.cookies


@pytest.mark.asyncio
async def test_subscription_guard_blocks_materials_when_inactive(
    client: AsyncClient,
    db_session,
    unique_email: str,
):
    """Проверка, что неактивная подписка блокирует доступ к материалам."""
    tokens, cookies = await register_and_login(client, unique_email)

    subscription = await db_session.scalar(
        select(Subscription).where(Subscription.organization_id == tokens["organization_id"])
    )
    assert subscription is not None
    subscription.status = SubscriptionStatus.BLOCKED
    await db_session.flush()

    response = await client.get(
        "/api/v1/materials",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        cookies=cookies,
    )
    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "AUTHORIZATION_ERROR"


@pytest.mark.asyncio
async def test_materials_search_and_listing(
    client: AsyncClient,
    unique_email: str,
):
    """Создание и поиск материалов с публикацией и FTS."""
    tokens, cookies = await register_and_login(client, unique_email)

    create_payload = {
        "title": "Инструкция по безопасности на производстве",
        "summary": "Краткое описание инструкции",
        "content": "Полный текст инструкции по охране труда и безопасности.",
        "type": "article",
        "status": "published",
        "category_id": None,
    }
    created = await client.post(
        "/api/v1/materials",
        json=create_payload,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    material_id = created.json()["id"]

    search = await client.get(
        "/api/v1/materials/search",
        params={"q": "безопасности"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        cookies=cookies,
    )
    assert search.status_code == 200
    data = search.json()
    assert data["total"] >= 1
    assert any(item["id"] == material_id for item in data["items"])
