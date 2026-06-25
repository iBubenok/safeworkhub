"""Версия материала: неизменяемый снимок версионируемых полей."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.user import User


class MaterialVersion(Base, UUIDMixin):
    """Снимок материала на момент правки (история версий).

    Снимок версионируемых полей хранится в JSON `snapshot`, поэтому добавление
    новых редактируемых полей не требует миграции этой таблицы — достаточно
    положить новый ключ в снимок (см. MaterialService._snapshot).
    """

    __tablename__ = "material_versions"

    material_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    editor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    change_note: Mapped[str | None] = mapped_column(String(500))
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    material: Mapped["Material"] = relationship(back_populates="versions")
    editor: Mapped["User | None"] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("material_id", "version_no", name="uq_material_version_no"),
        Index("ix_material_versions_material_id", "material_id"),
    )

    def __repr__(self) -> str:
        return f"<MaterialVersion material_id={self.material_id} v{self.version_no}>"
