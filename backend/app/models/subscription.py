"""Модели подписки и тарифов."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
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

    TRIAL = "trial"           # Пробный период
    ACTIVE = "active"         # Активная подписка
    PAST_DUE = "past_due"     # Просрочена оплата (grace period)
    CANCELLED = "cancelled"   # Отменена
    EXPIRED = "expired"       # Истекла


class Tariff(Base, IntegerPKMixin, TimestampMixin):
    """Тариф (план подписки).

    Определяет стоимость и лимиты для подписки организации.

    Attributes:
        id: Целочисленный ID.
        name: Название тарифа.
        description: Описание тарифа.
        max_users: Максимальное количество пользователей.
        price_monthly: Месячная стоимость.
        price_yearly: Годовая стоимость.
        features: JSON с дополнительными возможностями тарифа.
        is_active: Доступен ли тариф для новых подписок.
    """

    __tablename__ = "tariffs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    max_users: Mapped[int] = mapped_column(nullable=False, default=10)
    price_monthly: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    price_yearly: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Связи
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="tariff")

    def __repr__(self) -> str:
        return f"<Tariff {self.name}>"


class Subscription(Base, IntegerPKMixin, TimestampMixin):
    """Подписка организации.

    Связывает организацию с тарифом и отслеживает статус оплаты.

    Attributes:
        id: Целочисленный ID.
        organization_id: ID организации.
        tariff_id: ID тарифа.
        status: Текущий статус подписки.
        started_at: Дата начала подписки.
        expires_at: Дата окончания подписки.
        trial_ends_at: Дата окончания пробного периода.
    """

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
        default=datetime.utcnow,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="subscription")
    tariff: Mapped["Tariff"] = relationship(back_populates="subscriptions")

    __table_args__ = (
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_expires_at", "expires_at"),
    )

    @property
    def is_active(self) -> bool:
        """Проверка активности подписки."""
        return self.status in (SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE)

    def __repr__(self) -> str:
        return f"<Subscription org={self.organization_id} status={self.status}>"
