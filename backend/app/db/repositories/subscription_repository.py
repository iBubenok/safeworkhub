"""Репозитории для тарифов и подписок."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.models import Subscription, SubscriptionStatus, Tariff


class TariffRepository(BaseRepository[Tariff]):
    """Работа с тарифами подписки."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Tariff, session)

    async def get_by_code(self, code: str) -> Tariff | None:
        query = select(Tariff).where(Tariff.code == code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Tariff]:
        query = select(Tariff).where(Tariff.is_active.is_(True)).order_by(Tariff.id)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class SubscriptionRepository(BaseRepository[Subscription]):
    """Работа с подписками организаций."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Subscription, session)

    async def get_with_tariff(self, organization_id: int) -> Subscription | None:
        query = (
            select(Subscription)
            .where(Subscription.organization_id == organization_id)
            .options(selectinload(Subscription.tariff))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        subscription: Subscription,
        *,
        status: SubscriptionStatus,
        valid_until: datetime | None = None,
        trial_ends_at: datetime | None = None,
    ) -> Subscription:
        subscription.status = status
        subscription.valid_until = valid_until
        subscription.trial_ends_at = trial_ends_at or subscription.trial_ends_at
        await self.session.flush()
        return subscription
