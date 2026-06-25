"""Модель вложения материала (файлы шаблонов и др.)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.material import Material


class MaterialAttachment(Base, UUIDMixin, TimestampMixin):
    """Файл, прикреплённый к материалу (1:много).

    Общая таблица для любых типов материалов; сейчас используется шаблонами.
    Сам файл хранится в `FileStorage` под ключом `storage_key`; в БД — метаданные.
    """

    __tablename__ = "material_attachments"

    material_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    material: Mapped["Material"] = relationship(back_populates="attachments")

    __table_args__ = (Index("ix_material_attachments_material_id", "material_id"),)

    def __repr__(self) -> str:
        return f"<MaterialAttachment {self.filename} material_id={self.material_id}>"
