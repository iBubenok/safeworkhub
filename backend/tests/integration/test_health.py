"""
Интеграционные тесты для endpoint здоровья системы.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Проверка endpoint /api/v1/health."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_check_details(client: AsyncClient):
    """Проверка деталей в ответе health check."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    # Проверяем структуру ответа
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
