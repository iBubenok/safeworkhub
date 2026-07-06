"""Модели подмодуля «Чек-листы»: шаблон чек-листа и его пункты."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.organization import Organization
    from app.models.user import User


class ChecklistStatus(StrEnum):
    """Статус чек-листа."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ChecklistAnswerType(StrEnum):
    """Тип ответа на пункт чек-листа."""

    COMPLIANCE = "compliance"  # соответствует / не соответствует / не применимо
    YES_NO = "yes_no"
    TEXT = "text"
    NUMBER = "number"


class ChecklistNodeType(StrEnum):
    """Тип узла чек-листа: раздел (группа) или пункт (вопрос)."""

    GROUP = "group"
    ITEM = "item"


class ChecklistVisibility(StrEnum):
    """Видимость чек-листа (как у материалов)."""

    ORG = "org"  # только своя организация
    PUBLIC = "public"  # виден всем организациям


def _enum(enum_cls: type, name: str) -> Enum:
    """PG-enum со значениями по value (как в остальных моделях)."""
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


class Checklist(Base, UUIDMixin, TimestampMixin):
    """Шаблон чек-листа (создаётся владельцем организации через конструктор)."""

    __tablename__ = "checklists"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ChecklistStatus] = mapped_column(
        _enum(ChecklistStatus, "checklist_status"),
        nullable=False,
        default=ChecklistStatus.DRAFT,
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Счётчик использований (запусков проверок). Монотонный: не уменьшается при удалении прогона —
    # факт использования шаблона сохраняется.
    runs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Видимость: org — только своя организация, public — виден всем организациям.
    visibility: Mapped[ChecklistVisibility] = mapped_column(
        _enum(ChecklistVisibility, "checklist_visibility"),
        nullable=False,
        default=ChecklistVisibility.ORG,
    )

    organization: Mapped["Organization"] = relationship()
    author: Mapped["User"] = relationship(foreign_keys=[author_id])
    updated_by: Mapped["User | None"] = relationship(foreign_keys=[updated_by_id], lazy="selectin")
    items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="checklist",
        cascade="all, delete-orphan",
        order_by="ChecklistItem.sort_order",
    )

    __table_args__ = (
        Index("ix_checklists_org", "organization_id"),
        Index("ix_checklists_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Checklist {self.title}>"


class ChecklistItem(Base, UUIDMixin, TimestampMixin):
    """Пункт чек-листа (вопрос с типом ответа и опц. ссылкой на материал)."""

    __tablename__ = "checklist_items"

    checklist_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("checklists.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("checklist_items.id", ondelete="CASCADE"),
        index=True,
    )
    node_type: Mapped[ChecklistNodeType] = mapped_column(
        _enum(ChecklistNodeType, "checklist_node_type"),
        nullable=False,
        default=ChecklistNodeType.ITEM,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # У групп (разделов) типа ответа нет → nullable.
    answer_type: Mapped[ChecklistAnswerType | None] = mapped_column(_enum(ChecklistAnswerType, "checklist_answer_type"))
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text)
    # Подсказки редактора к вариантам ответа: {"<значение>": "<текст>"}.
    # Ключи — канонические значения (compliant/non_compliant/not_applicable, true/false).
    option_hints: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict, nullable=False)

    checklist: Mapped["Checklist"] = relationship(back_populates="items")
    references: Mapped[list["ChecklistItemReference"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="ChecklistItemReference.sort_order",
    )

    __table_args__ = (Index("ix_checklist_items_checklist_id", "checklist_id"),)

    def __repr__(self) -> str:
        return f"<ChecklistItem {self.text[:40]}>"


class ChecklistItemReference(Base, UUIDMixin):
    """Ссылка пункта чек-листа: материал из базы знаний и/или заметка (1:много)."""

    __tablename__ = "checklist_item_references"

    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("checklist_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    material_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="SET NULL"),
    )
    note: Mapped[str | None] = mapped_column(String(500))

    item: Mapped["ChecklistItem"] = relationship(back_populates="references")
    material: Mapped["Material | None"] = relationship(lazy="selectin")

    __table_args__ = (Index("ix_checklist_item_references_item_id", "item_id"),)

    def __repr__(self) -> str:
        return f"<ChecklistItemReference item={self.item_id}>"
