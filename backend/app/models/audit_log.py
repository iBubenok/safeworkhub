"""Модель аудита действий пользователей."""

from __future__ import annotations

from uuid import UUID
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin


class AuditLog(Base, UUIDMixin):
    """Аудит критичных действий."""

    __tablename__ = "audit_logs"

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("ix_audit_logs_org", "organization_id"),
        Index("ix_audit_logs_user", "user_id"),
        Index("ix_audit_logs_action", "action"),
    )
