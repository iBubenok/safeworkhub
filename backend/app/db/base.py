"""Базовые классы и миксины для SQLAlchemy моделей."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""

    pass


class UUIDMixin:
    """Миксин для UUID первичного ключа.

    Использует UUID v4, генерируемый на стороне приложения.
    """

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class IntegerPKMixin:
    """Миксин для целочисленного автоинкрементного первичного ключа."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class TimestampMixin:
    """Миксин для автоматических временных меток.

    Добавляет поля created_at и updated_at с автозаполнением.
    """

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
    """Миксин для мягкого удаления.

    Записи не удаляются физически, а помечаются временной меткой удаления.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Проверка, удалена ли запись."""
        return self.deleted_at is not None
