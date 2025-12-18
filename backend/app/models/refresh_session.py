"""Модель refresh-сессий для ротации токенов."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class RefreshSession(Base, UUIDMixin, TimestampMixin):
    """Refresh-сессия для пользователя.

    Содержит хэш токена и используется для ротации и отзыва.
    """

    __tablename__ = "refresh_sessions"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Связи
    user: Mapped["User"] = relationship(back_populates="refresh_sessions")

    __table_args__ = (
        Index("ix_refresh_sessions_user", "user_id"),
        Index("ix_refresh_sessions_family", "family_id"),
        Index("ix_refresh_sessions_expires", "expires_at"),
    )
