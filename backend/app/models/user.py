"""Модель пользователя."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.course import CourseAssignment
    from app.models.material import Material
    from app.models.organization import Organization, OrganizationUser
    from app.models.refresh_session import RefreshSession


class User(Base, UUIDMixin, TimestampMixin):
    """Пользователь системы."""

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
    primary_organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Связи
    organization_memberships: Mapped[list["OrganizationUser"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    owned_organizations: Mapped[list["Organization"]] = relationship(
        back_populates="owner",
        foreign_keys="[Organization.owner_id]",
    )
    materials: Mapped[list["Material"]] = relationship(
        back_populates="author",
        foreign_keys="[Material.author_id]",
    )
    course_assignments: Mapped[list["CourseAssignment"]] = relationship(back_populates="user")
    primary_organization: Mapped["Organization | None"] = relationship(foreign_keys="[User.primary_organization_id]")

    __table_args__ = (
        Index("ix_users_email_lower", "email"),
        Index("ix_users_primary_org", "primary_organization_id"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
