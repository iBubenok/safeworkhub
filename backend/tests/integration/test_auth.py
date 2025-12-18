"""Интеграционные тесты для аутентификации и ротации refresh-токенов."""

import pytest
from httpx import AsyncClient

from app.core.config import settings


def build_registration_payload(email: str) -> dict:
    """Сформировать тело запроса на регистрацию."""
    return {
        "organization_name": "Тестовая организация",
        "inn": "7728168971",
        "admin_email": email,
        "admin_password": "SuperSecure123!",
        "admin_name": "Тестовый Админ",
    }


@pytest.mark.asyncio
async def test_auth_flow_with_refresh_rotation(client: AsyncClient, unique_email: str):
    """Регистрация, логин, ротация refresh и защита от повторного использования."""
    register_payload = build_registration_payload(unique_email)
    register = await client.post("/api/v1/auth/register", json=register_payload)
    assert register.status_code == 201

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["admin_email"], "password": register_payload["admin_password"]},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["organization_id"] > 0
    assert "access_token" in tokens
    assert settings.refresh_token_cookie_name in login.cookies

    refresh = await client.post("/api/v1/auth/refresh", cookies=login.cookies)
    assert refresh.status_code == 200
    new_tokens = refresh.json()
    assert new_tokens["access_token"] != tokens["access_token"]

    # Повторное использование старого refresh должно быть заблокировано
    reused = await client.post(
        "/api/v1/auth/refresh",
        cookies={settings.refresh_token_cookie_name: login.cookies.get(settings.refresh_token_cookie_name)},
    )
    assert reused.status_code == 401

    logout = await client.post("/api/v1/auth/logout", cookies=refresh.cookies)
    assert logout.status_code == 204
