"""Модели подписки и тарифов."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IntegerPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class SubscriptionStatus(StrEnum):
    """Статусы подписки."""

    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class Tariff(Base, IntegerPKMixin, TimestampMixin):
    """Тариф (план подписки)."""

    __tablename__ = "tariffs"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    max_users: Mapped[int] = mapped_column(nullable=False, default=10)
    price_monthly: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_yearly: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Связи
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="tariff")

    def __repr__(self) -> str:
        return f"<Tariff {self.code}>"


class Subscription(Base, IntegerPKMixin, TimestampMixin):
    """Подписка организации."""

    __tablename__ = "subscriptions"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    tariff_id: Mapped[int] = mapped_column(
        ForeignKey("tariffs.id"),
        nullable=False,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.TRIAL,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="subscription")
    tariff: Mapped["Tariff"] = relationship(back_populates="subscriptions")

    __table_args__ = (
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_valid_until", "valid_until"),
    )

    @property
    def is_active(self) -> bool:
        """Проверка активности подписки."""
        return self.status in (SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE)

    def __repr__(self) -> str:
        return f"<Subscription org={self.organization_id} status={self.status}>"
