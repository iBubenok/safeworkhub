"""Репозиторий для работы с пользователями."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.models import User, OrganizationUser


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с пользователями.

    Расширяет базовый репозиторий специфичными методами
    для работы с пользователями.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Найти пользователя по email.

        Args:
            email: Email пользователя.

        Returns:
            Пользователь или None.
        """
        query = select(User).where(User.email == email.lower())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_organizations(self, user_id: UUID) -> User | None:
        """Получить пользователя с его организациями.

        Args:
            user_id: ID пользователя.

        Returns:
            Пользователь с загруженными организациями или None.
        """
        query = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.organization_memberships).selectinload(
                    OrganizationUser.organization
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        query_str: str,
        *,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = True,
    ) -> list[User]:
        """Поиск пользователей по email или имени.

        Args:
            query_str: Строка поиска.
            limit: Максимальное количество результатов.
            offset: Смещение.
            active_only: Искать только активных пользователей.

        Returns:
            Список найденных пользователей.
        """
        search_pattern = f"%{query_str}%"
        query = select(User).where(
            or_(
                User.email.ilike(search_pattern),
                User.name.ilike(search_pattern),
            )
        )

        if active_only:
            query = query.where(User.is_active == True)  # noqa: E712

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_organization(
        self,
        organization_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Получить пользователей организации.

        Args:
            organization_id: ID организации.
            limit: Максимальное количество.
            offset: Смещение.

        Returns:
            Список пользователей организации.
        """
        query = (
            select(User)
            .join(OrganizationUser)
            .where(OrganizationUser.organization_id == organization_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def is_email_taken(self, email: str, exclude_user_id: UUID | None = None) -> bool:
        """Проверить, занят ли email.

        Args:
            email: Email для проверки.
            exclude_user_id: ID пользователя для исключения из проверки.

        Returns:
            True если email занят.
        """
        query = select(User.id).where(User.email == email.lower())
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
