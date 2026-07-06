"""Модели подмодуля «Проверки»: проведённая по чек-листу проверка и её ответы.

Проверка — это снимок (snapshot) шаблона чек-листа на момент проведения: текст пунктов,
тип ответа и ссылки копируются в строки проверки. Так проведённая проверка остаётся
неизменяемым историческим документом, даже если шаблон позже отредактируют или удалят.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.checklist import ChecklistAnswerType

if TYPE_CHECKING:
    from app.models.user import User


class ChecklistRunStatus(StrEnum):
    """Статус проверки."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ChecklistRunResult(StrEnum):
    """Итог завершённой проверки."""

    PASSED = "passed"  # нарушений нет
    HAS_ISSUES = "has_issues"  # есть несоответствия


class ChecklistComplianceValue(StrEnum):
    """Значение ответа для пунктов типа «Соответствие»."""

    COMPLIANT = "compliant"  # соответствует
    NON_COMPLIANT = "non_compliant"  # не соответствует
    NOT_APPLICABLE = "not_applicable"  # не применимо


def _enum(enum_cls: type, name: str) -> Enum:
    """PG-enum со значениями по value (как в остальных моделях)."""
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


# Назначенные на проверку сотрудники (кроме создателя `conducted_by_id`): им также
# разрешено редактировать и завершать проверку. M2M «проверка ↔ пользователь».
checklist_run_assignees = Table(
    "checklist_run_assignees",
    Base.metadata,
    Column("run_id", PG_UUID(as_uuid=True), ForeignKey("checklist_runs.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_checklist_run_assignees_user_id", "user_id"),
)


class ChecklistRun(Base, UUIDMixin, TimestampMixin):
    """Проведённая по чек-листу проверка."""

    __tablename__ = "checklist_runs"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Ссылка на шаблон сохраняется для контекста, но проверка переживает его удаление.
    checklist_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("checklists.id", ondelete="SET NULL"),
    )
    checklist_title: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    conducted_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[ChecklistRunStatus] = mapped_column(
        _enum(ChecklistRunStatus, "checklist_run_status"),
        nullable=False,
        default=ChecklistRunStatus.IN_PROGRESS,
    )
    result: Mapped[ChecklistRunResult | None] = mapped_column(_enum(ChecklistRunResult, "checklist_run_result"))
    gradable_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compliant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    non_compliant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    not_applicable_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conducted_by: Mapped["User"] = relationship(foreign_keys=[conducted_by_id], lazy="selectin")
    assignees: Mapped[list["User"]] = relationship(secondary=checklist_run_assignees, lazy="selectin")
    answers: Mapped[list["ChecklistRunAnswer"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ChecklistRunAnswer.sort_order",
    )

    __table_args__ = (
        Index("ix_checklist_runs_org", "organization_id"),
        Index("ix_checklist_runs_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ChecklistRun {self.title or self.checklist_title}>"


class ChecklistRunAnswer(Base, UUIDMixin, TimestampMixin):
    """Ответ на пункт проверки (снимок пункта шаблона + введённое значение)."""

    __tablename__ = "checklist_run_answers"

    run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("checklist_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Снимок структуры шаблона (group_title — заголовок раздела пункта, если есть).
    group_title: Mapped[str | None] = mapped_column(String(500))
    item_text: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text)
    # Тот же Python-enum, что у пунктов шаблона, но отдельный PG-тип, чтобы не
    # дублировать CREATE TYPE существующего "checklist_answer_type".
    answer_type: Mapped[ChecklistAnswerType] = mapped_column(
        _enum(ChecklistAnswerType, "checklist_run_answer_type"),
        nullable=False,
    )
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Снимок ссылок пункта: [{"material_id": ..., "material_title": ..., "note": ...}].
    references: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    # Введённое значение в каноническом виде (код compliance / "true"|"false" / текст / число строкой).
    value: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)

    run: Mapped["ChecklistRun"] = relationship(back_populates="answers")

    __table_args__ = (Index("ix_checklist_run_answers_run_id", "run_id"),)

    def __repr__(self) -> str:
        return f"<ChecklistRunAnswer {self.item_text[:40]}>"
