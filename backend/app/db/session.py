"""Управление сессиями базы данных."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(
    str(settings.database_url),
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_pool_overflow,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,   # Переподключение каждый час
)

# Фабрика асинхронных сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД.

    Сессия автоматически коммитится при успешном завершении
    и откатывается при возникновении исключения.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    async with async_session_factory() as session:
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
    from app.db.base import Base
    from app.models import *  # noqa: F401,F403 — импорт всех моделей

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрытие соединений с базой данных."""
    await engine.dispose()
