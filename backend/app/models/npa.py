"""Деталь-таблица для типа материала «НПА» (нормативно-правовой акт)."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.material import NpaActKind, NpaLevel, NpaStatus

if TYPE_CHECKING:
    from app.models.material import Material


def _enum(enum_cls: type, name: str) -> Enum:
    """PG-enum со значениями по value (как в Material)."""
    return Enum(enum_cls, name=name, values_callable=lambda e: [m.value for m in e])


class Npa(Base):
    """Поля, специфичные для нормативно-правового акта (1:1 к базовому материалу)."""

    __tablename__ = "npa"

    material_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        primary_key=True,
    )
    act_kind: Mapped[NpaActKind] = mapped_column(_enum(NpaActKind, "npa_act_kind"), nullable=False)
    level: Mapped[NpaLevel | None] = mapped_column(_enum(NpaLevel, "npa_level"))
    act_status: Mapped[NpaStatus | None] = mapped_column(_enum(NpaStatus, "npa_status"))
    document_number: Mapped[str | None] = mapped_column(String(100))
    adoption_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date)
    revision_date: Mapped[date | None] = mapped_column(Date)
    issuing_authority: Mapped[str | None] = mapped_column(String(500))
    region: Mapped[str | None] = mapped_column(String(255))
    official_source_url: Mapped[str | None] = mapped_column(String(2000))

    material: Mapped["Material"] = relationship(back_populates="npa")

    def __repr__(self) -> str:
        return f"<Npa material_id={self.material_id}>"
