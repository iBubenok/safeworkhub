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


class _SessionState:
    """Хранение состояния движка и фабрики сессий без использования global."""

    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None


_state = _SessionState()


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Ленивая инициализация движка и фабрики сессий."""
    if _state.engine is None or _state.session_factory is None:
        settings = get_settings()
        engine = create_async_engine(
            str(settings.database_url),
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_pool_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        _state.engine = engine
        _state.session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    assert _state.session_factory is not None, "Фабрика сессий не инициализирована"
    return _state.session_factory


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Публичный доступ к фабрике сессий (для фоновых задач вне цикла запроса)."""
    return _get_session_factory()


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
    assert _state.engine is not None, "Движок БД не инициализирован"

    async with _state.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрытие соединений с базой данных."""
    if _state.engine is not None:
        await _state.engine.dispose()
    _state.engine = None
    _state.session_factory = None
