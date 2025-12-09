"""Модели организации и членства."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IntegerPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.subscription import Subscription


class Organization(Base, IntegerPKMixin, TimestampMixin):
    """Организация (компания-клиент).

    Организация является основной единицей для биллинга и управления доступом.
    Пользователи связаны с организацией через OrganizationUser.

    Attributes:
        id: Целочисленный автоинкрементный ID.
        name: Название организации.
        inn: ИНН организации (уникальный).
        description: Описание организации.
        logo_url: URL логотипа.
        created_at: Дата создания.
        updated_at: Дата последнего обновления.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))

    # Связи
    members: Mapped[list["OrganizationUser"]] = relationship(
        back_populates="organization",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="organization",
        uselist=False,
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_organizations_inn", "inn"),
        Index("ix_organizations_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name} (ИНН: {self.inn})>"


class OrganizationUser(Base, TimestampMixin):
    """Членство пользователя в организации.

    Промежуточная таблица для связи many-to-many между User и Organization
    с дополнительными атрибутами (роль, дата присоединения).

    Attributes:
        organization_id: ID организации.
        user_id: ID пользователя.
        role: Роль пользователя в организации.
        joined_at: Дата присоединения к организации.
    """

    __tablename__ = "organization_users"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="employee",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="organization_memberships")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
        Index("ix_organization_users_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<OrganizationUser org={self.organization_id} user={self.user_id} role={self.role}>"
