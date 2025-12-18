"""Интеграционные тесты для endpoint здоровья системы."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_and_readiness(client: AsyncClient):
    """Проверка liveness и readiness."""
    health = await client.get("/api/v1/health")
    assert health.status_code == 200

    health_data = health.json()
    assert health_data["status"] == "healthy"
    assert "version" in health_data
    assert health_data["environment"] == "testing"

    readiness = await client.get("/api/v1/ready")
    assert readiness.status_code == 200

    ready_data = readiness.json()
    assert ready_data["database"] in {"connected", "disconnected"}
    assert ready_data["cache"] in {"connected", "disconnected"}
    assert ready_data["status"] in {"ready", "not_ready"}
