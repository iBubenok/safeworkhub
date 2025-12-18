"""Модели системы обучения (LMS)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IntegerPKMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Course(Base, IntegerPKMixin, TimestampMixin):
    """Учебный курс (вариант A: назначение пользователю и отслеживание прогресса)."""

    __tablename__ = "courses"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="courses")
    modules: Mapped[list["CourseModule"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseModule.sort_order",
    )
    assignments: Mapped[list["CourseAssignment"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_courses_is_published", "is_published"),
        Index("ix_courses_org", "organization_id"),
    )

    def __repr__(self) -> str:
        return f"<Course {self.title}>"


class CourseModule(Base, IntegerPKMixin, TimestampMixin):
    """Модуль (урок) курса."""

    __tablename__ = "course_modules"

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Связи
    course: Mapped["Course"] = relationship(back_populates="modules")

    __table_args__ = (
        Index("ix_course_modules_course_id", "course_id"),
    )

    def __repr__(self) -> str:
        return f"<CourseModule {self.title}>"


class AssignmentStatus(StrEnum):
    """Статус прохождения курса пользователем."""

    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class CourseAssignment(Base, UUIDMixin, TimestampMixin):
    """Назначение курса пользователю и фиксация прогресса."""

    __tablename__ = "course_assignments"

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="course_assignment_status"),
        nullable=False,
        default=AssignmentStatus.ASSIGNED,
    )
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Связи
    course: Mapped["Course"] = relationship(back_populates="assignments")
    user: Mapped["User"] = relationship(back_populates="course_assignments")
    organization: Mapped["Organization"] = relationship()

    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_course_assignment"),
        Index("ix_course_assignments_org", "organization_id"),
        Index("ix_course_assignments_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<CourseAssignment course={self.course_id} user={self.user_id} status={self.status}>"
