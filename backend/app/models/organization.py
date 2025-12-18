"""Модели организации и членства."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IntegerPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.material import Category, Material
    from app.models.subscription import Subscription
    from app.models.user import User


class OrgRole(StrEnum):
    """Роли пользователей внутри организации."""

    ORG_OWNER = "org_owner"
    MEMBER = "member"


class Organization(Base, IntegerPKMixin, TimestampMixin):
    """Организация (компания-клиент)."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # Связи
    members: Mapped[list["OrganizationUser"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    categories: Mapped[list["Category"]] = relationship(back_populates="organization")
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )
    materials: Mapped[list["Material"]] = relationship(back_populates="organization")
    courses: Mapped[list["Course"]] = relationship(back_populates="organization")
    owner: Mapped["User | None"] = relationship(
        back_populates="owned_organizations",
        foreign_keys=[owner_id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_organizations_inn", "inn"),
        Index("ix_organizations_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name} (ИНН: {self.inn})>"


class OrganizationUser(Base, TimestampMixin):
    """Членство пользователя в организации."""

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
    role: Mapped[OrgRole] = mapped_column(
        String(50),
        nullable=False,
        default=OrgRole.MEMBER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="organization_memberships")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
        Index("ix_organization_users_user_id", "user_id"),
        Index("ix_organization_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<OrganizationUser org={self.organization_id} user={self.user_id} role={self.role}>"
