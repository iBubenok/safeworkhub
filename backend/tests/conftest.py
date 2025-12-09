"""
Конфигурация pytest для SafeWorkHub.

Содержит общие фикстуры и настройки для всех тестов.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings


# Переопределяем URL базы данных для тестов
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    settings.POSTGRES_DB, f"{settings.POSTGRES_DB}_test"
) if hasattr(settings, 'DATABASE_URL') else "postgresql+asyncpg://test:test@localhost:5432/test"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создаёт event loop для всей сессии тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Создаёт тестовый движок базы данных."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Создаёт сессию базы данных для теста."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Создаёт тестовый HTTP-клиент."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def user_data() -> dict[str, Any]:
    """Возвращает данные тестового пользователя."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Тестовый Пользователь",
    }


@pytest.fixture
def admin_user_data() -> dict[str, Any]:
    """Возвращает данные тестового администратора."""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "name": "Администратор Системы",
        "is_admin": True,
    }
