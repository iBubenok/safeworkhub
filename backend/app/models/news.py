"""Деталь-таблица для типа материала «Новость»."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.material import Material


class News(Base):
    """Поля, специфичные для новости (1:1 к базовому материалу)."""

    __tablename__ = "news"

    material_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        primary_key=True,
    )
    source_url: Mapped[str | None] = mapped_column(String(2000))
    event_date: Mapped[date | None] = mapped_column(Date)
    cover_image_url: Mapped[str | None] = mapped_column(String(2000))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    material: Mapped["Material"] = relationship(back_populates="news")

    def __repr__(self) -> str:
        return f"<News material_id={self.material_id}>"
