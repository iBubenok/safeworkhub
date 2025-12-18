"""Управление сессиями базы данных."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.base import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Ленивая инициализация движка и фабрики сессий."""
    global _engine, _session_factory

    if _engine is None or _session_factory is None:
        settings = get_settings()
        _engine = create_async_engine(
            str(settings.database_url),
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_pool_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД.

    Сессия автоматически коммитится при успешном завершении
    и откатывается при возникновении исключения.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    session_factory = _get_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Инициализация базы данных.

    Создаёт все таблицы, если они не существуют.
    Используется только для разработки, в production применяются миграции.
    """
    _get_session_factory()
    assert _engine is not None, "Движок БД не инициализирован"

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрытие соединений с базой данных."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
