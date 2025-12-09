# Архитектура работы с базой данных

## Обзор

Документ описывает архитектуру слоя данных SafeWorkHub: модели, доступ к данным, управление транзакциями, миграции и оптимизацию запросов.

## Технологический стек

| Компонент | Технология | Версия |
|-----------|-----------|--------|
| СУБД | PostgreSQL | 16+ |
| ORM | SQLAlchemy | 2.0+ |
| Асинхронный драйвер | asyncpg | 0.29+ |
| Миграции | Alembic | 1.13+ |
| Пул соединений | SQLAlchemy AsyncSession | — |

## Архитектура слоя данных

### Слоистая структура

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│                 (Бизнес-логика, координация)                │
├─────────────────────────────────────────────────────────────┤
│                    Repository Layer                          │
│              (Абстракция доступа к данным)                  │
├─────────────────────────────────────────────────────────────┤
│                     ORM Layer                                │
│                (SQLAlchemy Models)                          │
├─────────────────────────────────────────────────────────────┤
│                   Session Layer                              │
│           (AsyncSession, Unit of Work)                      │
├─────────────────────────────────────────────────────────────┤
│                  Connection Pool                             │
│                    (asyncpg)                                │
├─────────────────────────────────────────────────────────────┤
│                    PostgreSQL                                │
└─────────────────────────────────────────────────────────────┘
```

### Принципы

1. **Репозитории** инкапсулируют логику доступа к данным
2. **Сервисы** координируют бизнес-операции, не знают о SQL
3. **Session** управляется на уровне запроса (request scope)
4. **Транзакции** явные, управляются через Unit of Work

## Модель данных

### Доменные сущности (ER-диаграмма)

```
┌─────────────────┐         ┌─────────────────────┐
│   Organization  │────────▶│ OrganizationUser    │
├─────────────────┤         ├─────────────────────┤
│ id              │         │ id                  │
│ name            │         │ organization_id FK  │
│ inn             │◀────────│ user_id FK          │
│ created_at      │         │ role_id FK          │
│ updated_at      │         │ joined_at           │
└─────────────────┘         └─────────────────────┘
        │                           │
        │                           ▼
        │                   ┌─────────────────┐
        │                   │      User       │
        │                   ├─────────────────┤
        │                   │ id              │
        │                   │ email           │
        │                   │ password_hash   │
        │                   │ name            │
        │                   │ is_active       │
        │                   │ created_at      │
        │                   └─────────────────┘
        │
        ▼
┌─────────────────┐         ┌─────────────────┐
│  Subscription   │────────▶│     Tariff      │
├─────────────────┤         ├─────────────────┤
│ id              │         │ id              │
│ organization_id │         │ name            │
│ tariff_id FK    │         │ max_users       │
│ status          │         │ price_monthly   │
│ started_at      │         │ price_yearly    │
│ expires_at      │         │ features JSONB  │
└─────────────────┘         └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│    Material     │         │   Category      │
├─────────────────┤         ├─────────────────┤
│ id              │────────▶│ id              │
│ title           │         │ name            │
│ content         │         │ parent_id FK    │
│ type            │         │ sort_order      │
│ category_id FK  │         └─────────────────┘
│ published_at    │
│ search_vector   │         ┌─────────────────┐
└─────────────────┘         │   Document      │
                            ├─────────────────┤
┌─────────────────┐         │ id              │
│     Course      │         │ title           │
├─────────────────┤         │ file_path       │
│ id              │         │ format          │
│ title           │         │ material_id FK  │
│ description     │         │ downloads_count │
│ duration_hours  │         └─────────────────┘
│ is_published    │
└─────────────────┘
        │
        ▼
┌─────────────────┐         ┌─────────────────┐
│     Module      │────────▶│      Test       │
├─────────────────┤         ├─────────────────┤
│ id              │         │ id              │
│ course_id FK    │         │ module_id FK    │
│ title           │         │ title           │
│ content         │         │ time_limit_min  │
│ sort_order      │         │ passing_score   │
│ duration_min    │         │ questions JSONB │
└─────────────────┘         └─────────────────┘
                                    │
                                    ▼
                            ┌─────────────────┐
                            │  TestAttempt    │
                            ├─────────────────┤
                            │ id              │
                            │ test_id FK      │
                            │ user_id FK      │
                            │ score           │
                            │ passed          │
                            │ started_at      │
                            │ completed_at    │
                            │ answers JSONB   │
                            └─────────────────┘
```

### Базовые классы моделей

```python
# app/db/base.py

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


class UUIDMixin:
    """Миксин для UUID первичного ключа."""

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class IntegerPKMixin:
    """Миксин для целочисленного первичного ключа."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class TimestampMixin:
    """Миксин для временных меток создания и обновления."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Миксин для мягкого удаления."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
```

### Примеры моделей

```python
# app/models/user.py

from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """Модель пользователя."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # Связи
    organization_memberships: Mapped[list["OrganizationUser"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# app/models/organization.py

from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IntegerPKMixin, TimestampMixin


class Organization(Base, IntegerPKMixin, TimestampMixin):
    """Модель организации."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Связи
    users: Mapped[list["OrganizationUser"]] = relationship(
        back_populates="organization",
        lazy="selectin",
    )
    subscription: Mapped["Subscription"] = relationship(
        back_populates="organization",
        uselist=False,
    )

    # Индексы
    __table_args__ = (
        Index("ix_organizations_inn", "inn"),
        Index("ix_organizations_name_gin", "name", postgresql_using="gin"),
    )
```

## Управление сессиями

### Конфигурация пула соединений

```python
# app/db/session.py

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


# Создание асинхронного движка
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Логирование SQL в debug-режиме
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_pool_overflow,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,   # Переподключение каждый час
)

# Фабрика сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Рекомендуемые параметры пула

| Окружение | pool_size | max_overflow | Примечание |
|-----------|-----------|--------------|------------|
| Development | 5 | 5 | Минимум для разработки |
| Staging | 10 | 10 | Тестирование нагрузки |
| Production | 20 | 10 | На один инстанс API |

**Формула**: `total_connections = instances * (pool_size + max_overflow)`

Для PostgreSQL по умолчанию `max_connections = 100`. При 3 инстансах API и pool_size=20:
`3 * (20 + 10) = 90` — в пределах лимита.

## Паттерн Repository

### Базовый репозиторий

```python
# app/db/repositories/base.py

from typing import Generic, TypeVar, Type
from uuid import UUID

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Базовый репозиторий с CRUD-операциями."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID | int) -> ModelType | None:
        """Получить запись по ID."""
        return await self.session.get(self.model, id)

    async def get_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelType]:
        """Получить все записи с пагинацией."""
        query = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Создать новую запись."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID | int, **kwargs) -> ModelType | None:
        """Обновить запись по ID."""
        instance = await self.get_by_id(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID | int) -> bool:
        """Удалить запись по ID."""
        instance = await self.get_by_id(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True


class SoftDeleteRepository(BaseRepository[ModelType]):
    """Репозиторий с поддержкой мягкого удаления."""

    async def get_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        """Получить все записи (по умолчанию без удалённых)."""
        query = select(self.model)
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, id: UUID | int) -> bool:
        """Мягкое удаление."""
        from datetime import datetime, timezone

        instance = await self.get_by_id(id)
        if not instance:
            return False
        instance.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True
```

### Специализированный репозиторий

```python
# app/db/repositories/user_repository.py

from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.models import User


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Найти пользователя по email."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_organizations(self, user_id: UUID) -> User | None:
        """Получить пользователя с его организациями."""
        query = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.organization_memberships)
                .selectinload(OrganizationUser.organization)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        query_str: str,
        *,
        limit: int = 20,
    ) -> list[User]:
        """Поиск пользователей по email или имени."""
        search_pattern = f"%{query_str}%"
        query = (
            select(User)
            .where(
                or_(
                    User.email.ilike(search_pattern),
                    User.name.ilike(search_pattern),
                )
            )
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_users_count(self, organization_id: int) -> int:
        """Количество активных пользователей организации."""
        query = (
            select(func.count())
            .select_from(User)
            .join(OrganizationUser)
            .where(
                OrganizationUser.organization_id == organization_id,
                User.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()
```

## Транзакции

### Автоматическое управление (рекомендуется)

Транзакция автоматически управляется в `get_session()`:

```python
@router.post("/users")
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    # Всё в одной транзакции
    user = await user_service.create(session, data)
    await notification_service.send_welcome(session, user)
    # Commit при успешном выходе, rollback при исключении
    return user
```

### Явное управление

Для сложных сценариев с вложенными транзакциями:

```python
async def complex_operation(session: AsyncSession):
    """Операция с явным управлением транзакцией."""

    # Savepoint для вложенной транзакции
    async with session.begin_nested():
        try:
            await operation_1(session)
            await operation_2(session)
        except SpecificError:
            # Откат только вложенной транзакции
            raise

    # Продолжение основной транзакции
    await operation_3(session)
```

### Unit of Work

```python
# app/db/unit_of_work.py

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepository, OrganizationRepository


class UnitOfWork:
    """Единица работы для координации репозиториев."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session: AsyncSession = self._session_factory()
        self.users = UserRepository(self._session)
        self.organizations = OrganizationRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


# Использование
async def register_organization(data: OrganizationCreate) -> Organization:
    async with UnitOfWork(session_factory) as uow:
        org = await uow.organizations.create(**data.dict())
        user = await uow.users.create(
            organization_id=org.id,
            **admin_data.dict(),
        )
        await uow.commit()
        return org
```

## Полнотекстовый поиск

### Настройка PostgreSQL FTS

```python
# app/models/material.py

from sqlalchemy import String, Text, Index, Computed
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.db.base import Base, UUIDMixin, TimestampMixin


class Material(Base, UUIDMixin, TimestampMixin):
    """Материал базы знаний с полнотекстовым поиском."""

    __tablename__ = "materials"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Вычисляемый столбец для поиска
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('russian', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('russian', coalesce(content, '')), 'B')",
            persisted=True,
        ),
    )

    __table_args__ = (
        # GIN-индекс для быстрого поиска
        Index(
            "ix_materials_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
        # Индекс для триграммного поиска (опечатки)
        Index(
            "ix_materials_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )
```

### Репозиторий с поиском

```python
# app/db/repositories/material_repository.py

from sqlalchemy import select, func, desc
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.models import Material


class MaterialRepository(BaseRepository[Material]):
    """Репозиторий материалов с полнотекстовым поиском."""

    async def search(
        self,
        query: str,
        *,
        material_type: str | None = None,
        category_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Material], int]:
        """Полнотекстовый поиск материалов."""

        # Преобразование запроса в tsquery
        ts_query = func.plainto_tsquery("russian", query)

        # Базовый запрос с ранжированием
        search_query = (
            select(
                Material,
                func.ts_rank(Material.search_vector, ts_query).label("rank"),
            )
            .where(Material.search_vector.op("@@")(ts_query))
        )

        # Фильтры
        if material_type:
            search_query = search_query.where(Material.type == material_type)
        if category_id:
            search_query = search_query.where(Material.category_id == category_id)

        # Подсчёт общего количества
        count_query = select(func.count()).select_from(search_query.subquery())
        total = await self.session.scalar(count_query)

        # Результаты с пагинацией
        search_query = (
            search_query
            .order_by(desc("rank"))
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(search_query)
        materials = [row[0] for row in result.all()]

        return materials, total

    async def get_search_highlights(
        self,
        material_id: UUID,
        query: str,
    ) -> dict[str, str]:
        """Получить подсвеченные фрагменты для результата поиска."""

        ts_query = func.plainto_tsquery("russian", query)

        result = await self.session.execute(
            select(
                func.ts_headline(
                    "russian",
                    Material.title,
                    ts_query,
                    "StartSel=<mark>, StopSel=</mark>, MaxWords=50",
                ).label("title_highlight"),
                func.ts_headline(
                    "russian",
                    Material.content,
                    ts_query,
                    "StartSel=<mark>, StopSel=</mark>, MaxFragments=3, MaxWords=30",
                ).label("content_highlight"),
            ).where(Material.id == material_id)
        )

        row = result.one_or_none()
        if row:
            return {
                "title": row.title_highlight,
                "content": row.content_highlight,
            }
        return {}
```

## Миграции

### Конфигурация Alembic

```ini
# alembic.ini

[alembic]
script_location = app/db/migrations
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]
hooks = ruff
ruff.type = exec
ruff.executable = ruff
ruff.options = format REVISION_SCRIPT_FILENAME
```

```python
# app/db/migrations/env.py

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base
from app.models import *  # noqa: F401,F403 — импорт всех моделей

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Миграции в offline-режиме (генерация SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Миграции в online-режиме (async)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск async-миграций."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Правила миграций

1. **Одна миграция — одно логическое изменение**
2. **Обязательно реализовать downgrade**
3. **Data migrations отдельно от schema migrations**
4. **Не изменять применённые миграции**

### Пример миграции

```python
# app/db/migrations/versions/20240115_1200_add_users_table.py

"""Добавление таблицы пользователей.

Revision ID: abc123
Revises:
Create Date: 2024-01-15 12:00:00.000000
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "abc123"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
```

## Оптимизация производительности

### Индексы

| Тип | Когда использовать | Пример |
|-----|-------------------|--------|
| B-tree | Сравнения, сортировка, уникальность | `email`, `created_at` |
| GIN | Полнотекстовый поиск, JSONB, массивы | `search_vector`, `tags` |
| GiST | Геоданные, диапазоны | `location`, `period` |
| Hash | Только equality (редко) | — |

### N+1 Problem

```python
# Плохо: N+1 запросов
users = await session.execute(select(User))
for user in users.scalars():
    # Каждый раз новый запрос
    print(user.organization_memberships)

# Хорошо: eager loading
users = await session.execute(
    select(User).options(selectinload(User.organization_memberships))
)
for user in users.scalars():
    # Данные уже загружены
    print(user.organization_memberships)
```

### Стратегии загрузки связей

| Стратегия | Когда использовать |
|-----------|-------------------|
| `selectinload` | Коллекции, when accessing all items |
| `joinedload` | Единичные связи (one-to-one, many-to-one) |
| `subqueryload` | Большие коллекции, избежание картезианского произведения |
| `lazyload` | Редко используемые связи (осторожно с N+1) |

### Кэширование

```python
# Кэширование на уровне репозитория
import hashlib
from functools import wraps
from typing import Callable, TypeVar

from redis.asyncio import Redis

T = TypeVar("T")


def cached(ttl: int = 300):
    """Декоратор для кэширования результатов."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> T:
            # Генерация ключа кэша
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Попытка получить из кэша
            cached_value = await self.redis.get(cache_key)
            if cached_value:
                return deserialize(cached_value)

            # Выполнение и кэширование
            result = await func(self, *args, **kwargs)
            await self.redis.setex(cache_key, ttl, serialize(result))
            return result

        return wrapper

    return decorator


class MaterialRepository(BaseRepository[Material]):
    def __init__(self, session: AsyncSession, redis: Redis):
        super().__init__(Material, session)
        self.redis = redis

    @cached(ttl=600)  # 10 минут
    async def get_popular_materials(self, limit: int = 10) -> list[Material]:
        """Популярные материалы (кэшируются)."""
        ...
```

### EXPLAIN ANALYZE

```python
# Утилита для анализа запросов в development
async def explain_query(session: AsyncSession, query):
    """Вывод плана выполнения запроса."""
    from sqlalchemy import text

    explain_query = text(f"EXPLAIN ANALYZE {query.compile(compile_kwargs={'literal_binds': True})}")
    result = await session.execute(explain_query)
    for row in result:
        print(row[0])
```

## Мониторинг

### Метрики БД

Собираемые метрики:
- Количество соединений (активных/idle/waiting)
- Время выполнения запросов (p50, p95, p99)
- Количество запросов в секунду
- Cache hit ratio
- Размер таблиц и индексов
- Dead tuples (необходимость VACUUM)

### Логирование медленных запросов

```python
# В PostgreSQL: postgresql.conf
log_min_duration_statement = 100  # мс

# В SQLAlchemy: событие before_cursor_execute
from sqlalchemy import event
import time


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start_time"].pop(-1)
    if total > 0.1:  # 100ms
        logger.warning(
            "Медленный запрос",
            duration_ms=total * 1000,
            statement=statement[:500],
        )
```
