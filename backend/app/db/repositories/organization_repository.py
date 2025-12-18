"""Репозиторий для работы с организациями."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.models import Organization, OrganizationUser, Subscription


class OrganizationRepository(BaseRepository[Organization]):
    """Репозиторий для работы с организациями."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Organization, session)

    async def get_by_inn(self, inn: str) -> Organization | None:
        """Найти организацию по ИНН.

        Args:
            inn: ИНН организации.

        Returns:
            Организация или None.
        """
        query = select(Organization).where(Organization.inn == inn)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_subscription(self, organization_id: int) -> Organization | None:
        """Получить организацию с подпиской.

        Args:
            organization_id: ID организации.

        Returns:
            Организация с загруженной подпиской или None.
        """
        query = (
            select(Organization)
            .where(Organization.id == organization_id)
            .options(selectinload(Organization.subscription).selectinload(Subscription.tariff))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_users_count(self, organization_id: int) -> int:
        """Получить количество пользователей организации.

        Args:
            organization_id: ID организации.

        Returns:
            Количество пользователей.
        """
        query = (
            select(func.count())
            .select_from(OrganizationUser)
            .where(
                OrganizationUser.organization_id == organization_id,
                OrganizationUser.is_active.is_(True),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def is_inn_taken(self, inn: str, exclude_id: int | None = None) -> bool:
        """Проверить, занят ли ИНН.

        Args:
            inn: ИНН для проверки.
            exclude_id: ID организации для исключения.

        Returns:
            True если ИНН занят.
        """
        query = select(Organization.id).where(Organization.inn == inn)
        if exclude_id:
            query = query.where(Organization.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def set_owner(self, organization_id: int, user_id: UUID) -> None:
        """Назначить владельца организации."""
        organization = await self.get_by_id(organization_id)
        if organization:
            organization.owner_id = user_id
            await self.session.flush()

    async def search(
        self,
        query_str: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Organization]:
        """Поиск организаций по названию или ИНН.

        Args:
            query_str: Строка поиска.
            limit: Максимальное количество.
            offset: Смещение.

        Returns:
            Список организаций.
        """
        search_pattern = f"%{query_str}%"
        query = (
            select(Organization)
            .where(Organization.name.ilike(search_pattern) | Organization.inn.ilike(search_pattern))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
