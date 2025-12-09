"""Модель пользователя."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import OrganizationUser


class User(Base, UUIDMixin, TimestampMixin):
    """Пользователь системы.

    Пользователь может состоять в нескольких организациях
    с разными ролями через промежуточную таблицу OrganizationUser.

    Attributes:
        id: Уникальный идентификатор (UUID).
        email: Email (уникальный, используется для входа).
        password_hash: Хэш пароля (Argon2).
        name: Полное имя пользователя.
        is_active: Активен ли пользователь.
        is_superuser: Имеет ли права суперпользователя.
        created_at: Дата создания.
        updated_at: Дата последнего обновления.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Связи
    organization_memberships: Mapped[list["OrganizationUser"]] = relationship(
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_users_email_lower", "email"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
