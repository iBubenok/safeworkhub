"""Общие фикстуры для интеграционных тестов."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from sqlalchemy.pool import NullPool

# Настройки окружения для тестов должны быть заданы до импорта приложения
os.environ["SECRET_KEY"] = os.getenv(
    "TEST_SECRET_KEY",
    "test-secret-key-change-me-0123456789abcdef123456",
)
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://safeworkhub:safeworkhub_dev@localhost:5432/safeworkhub_test",
)
os.environ["APP_ENV"] = "testing"
os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app

get_settings.cache_clear()
settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создаёт event loop для всей сессии тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def _ensure_database(url_str: str) -> None:
    """Создать тестовую БД, если её нет, и очистить перед стартом."""
    url = make_url(url_str)
    database = url.database
    assert database is not None, "Не задано имя БД для тестов"

    conn = await asyncpg.connect(
        user=url.username,
        password=url.password or None,
        host=url.host or "localhost",
        port=url.port or 5432,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", database)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{database}" OWNER "{url.username}"')
        else:
            await conn.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=$1",
                database,
            )
    finally:
        await conn.close()


async def _drop_database(url_str: str) -> None:
    """Удалить тестовую БД после завершения тестов."""
    url = make_url(url_str)
    conn = await asyncpg.connect(
        user=url.username,
        password=url.password or None,
        host=url.host or "localhost",
        port=url.port or 5432,
        database="postgres",
    )
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Поднимает отдельный движок БД для тестов."""
    database_url = settings.database_url
    await _ensure_database(str(database_url))

    engine = create_async_engine(
        str(database_url),
        poolclass=NullPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Сессия БД для теста."""
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with session_factory() as session:
        table_names = ", ".join(table.name for table in Base.metadata.tables.values())
        if table_names:
            await session.execute(
                text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"),
            )
            await session.commit()
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент FastAPI c переопределённой сессией БД."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def unique_email() -> str:
    """Генерирует уникальный email для тестов."""
    return f"user_{uuid4().hex}@example.com"
