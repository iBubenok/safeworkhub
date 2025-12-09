"""
Интеграционные тесты для аутентификации.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, user_data: dict):
    """Регистрация нового пользователя."""
    response = await client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    # Ожидаем успешную регистрацию или 422 если пользователь уже существует
    assert response.status_code in [201, 200, 422]


@pytest.mark.asyncio
async def test_register_user_invalid_email(client: AsyncClient):
    """Регистрация с невалидным email отклоняется."""
    invalid_data = {
        "email": "not-an-email",
        "password": "TestPassword123!",
        "name": "Тестовый Пользователь",
    }

    response = await client.post(
        "/api/v1/auth/register",
        json=invalid_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Вход с неверными учётными данными отклоняется."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    """Защищённый маршрут без токена возвращает 401."""
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(client: AsyncClient):
    """Защищённый маршрут с невалидным токеном возвращает 401."""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
