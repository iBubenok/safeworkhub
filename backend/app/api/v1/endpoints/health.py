"""Эндпоинты мониторинга здоровья сервиса."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session

router = APIRouter()


class HealthResponse(BaseModel):
    """Ответ проверки здоровья."""

    status: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Ответ проверки готовности."""

    status: str
    database: str
    cache: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Проверка здоровья сервиса (liveness probe).

    Возвращает базовую информацию о состоянии сервиса.
    Используется Kubernetes для проверки, что контейнер работает.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    session: AsyncSession = Depends(get_session),
) -> ReadinessResponse:
    """Проверка готовности сервиса (readiness probe).

    Проверяет подключение к базе данных и другим зависимостям.
    Используется Kubernetes для определения готовности принимать трафик.
    """
    # Проверка БД
    db_status = "connected"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    # Проверка Redis (упрощённо — можно расширить)
    cache_status = "connected"  # TODO: реальная проверка Redis

    overall_status = "ready" if db_status == "connected" else "not_ready"

    return ReadinessResponse(
        status=overall_status,
        database=db_status,
        cache=cache_status,
    )
