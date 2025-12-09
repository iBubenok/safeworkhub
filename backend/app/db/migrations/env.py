"""Конфигурация окружения Alembic для миграций."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base

# Импорт всех моделей для автогенерации миграций
from app.models import *  # noqa: F401,F403

# Конфигурация Alembic
config = context.config

# Установка URL базы данных из настроек
config.set_main_option("sqlalchemy.url", str(settings.database_url))

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автогенерации
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме.

    Генерирует SQL-скрипты без подключения к БД.
    Используется для проверки миграций или применения вручную.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполнение миграций с использованием соединения."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запуск миграций в async-режиме."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск миграций в online-режиме.

    Подключается к БД и применяет миграции.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
