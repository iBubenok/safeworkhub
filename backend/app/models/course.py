"""Модели системы обучения (LMS)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IntegerPKMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Course(Base, IntegerPKMixin, TimestampMixin):
    """Учебный курс.

    Курс состоит из модулей, которые пользователь проходит последовательно.

    Attributes:
        id: Целочисленный ID.
        title: Название курса.
        description: Описание курса.
        duration_hours: Расчётная продолжительность в часах.
        is_published: Опубликован ли курс.
        thumbnail_url: URL превью-изображения.
    """

    __tablename__ = "courses"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))

    # Связи
    modules: Mapped[list["Module"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Module.sort_order",
    )

    __table_args__ = (
        Index("ix_courses_is_published", "is_published"),
    )

    def __repr__(self) -> str:
        return f"<Course {self.title}>"


class Module(Base, IntegerPKMixin, TimestampMixin):
    """Модуль (урок) курса.

    Модуль содержит контент для изучения и может иметь связанный тест.

    Attributes:
        id: Целочисленный ID.
        course_id: ID курса.
        title: Название модуля.
        content: Содержимое модуля (HTML).
        sort_order: Порядок в курсе.
        duration_minutes: Расчётная продолжительность в минутах.
    """

    __tablename__ = "modules"

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
    test: Mapped["Test | None"] = relationship(
        back_populates="module",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_modules_course_id", "course_id"),
    )

    def __repr__(self) -> str:
        return f"<Module {self.title}>"


class Test(Base, IntegerPKMixin, TimestampMixin):
    """Тест для модуля курса.

    Содержит вопросы в формате JSON и настройки прохождения.

    Attributes:
        id: Целочисленный ID.
        module_id: ID модуля.
        title: Название теста.
        description: Описание теста.
        time_limit_minutes: Ограничение времени (0 = без ограничения).
        passing_score: Минимальный балл для прохождения (%).
        max_attempts: Максимальное количество попыток (0 = без ограничения).
        questions: JSON-массив вопросов.
    """

    __tablename__ = "tests"

    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    questions: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    # Связи
    module: Mapped["Module"] = relationship(back_populates="test")
    attempts: Mapped[list["TestAttempt"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Test {self.title}>"


class TestAttempt(Base, UUIDMixin, TimestampMixin):
    """Попытка прохождения теста.

    Фиксирует результат прохождения теста пользователем.

    Attributes:
        id: UUID попытки.
        test_id: ID теста.
        user_id: ID пользователя.
        score: Набранный балл (%).
        passed: Пройден ли тест.
        started_at: Время начала.
        completed_at: Время завершения.
        answers: JSON с ответами пользователя.
    """

    __tablename__ = "test_attempts"

    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Связи
    test: Mapped["Test"] = relationship(back_populates="attempts")

    __table_args__ = (
        Index("ix_test_attempts_test_id", "test_id"),
        Index("ix_test_attempts_user_id", "user_id"),
        Index("ix_test_attempts_passed", "passed"),
    )

    def __repr__(self) -> str:
        return f"<TestAttempt test={self.test_id} user={self.user_id} passed={self.passed}>"
