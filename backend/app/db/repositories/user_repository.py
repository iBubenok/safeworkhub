"""Репозиторий для работы с пользователями."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.models import OrganizationUser, OrgRole, User


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с пользователями и членствами организаций."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Найти пользователя по email."""
        query = select(User).where(User.email == email.lower())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_memberships(self, user_id: UUID) -> User | None:
        """Получить пользователя с загруженными членствами."""
        query = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.organization_memberships).selectinload(OrganizationUser.organization))
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
        """Поиск пользователей по email или имени."""
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
    ) -> list[tuple[User, OrgRole]]:
        """Получить пользователей организации вместе с их ролью в ней."""
        query = (
            select(User, OrganizationUser.role)
            .join(OrganizationUser, OrganizationUser.user_id == User.id)
            .where(
                OrganizationUser.organization_id == organization_id,
                OrganizationUser.is_active.is_(True),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    async def is_email_taken(
        self,
        email: str,
        exclude_user_id: UUID | None = None,
    ) -> bool:
        """Проверить, занят ли email."""
        query = select(User.id).where(User.email == email.lower())
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def add_membership(
        self,
        user_id: UUID,
        organization_id: int,
        role: OrgRole,
    ) -> OrganizationUser:
        """Добавить пользователя в организацию с ролью."""
        membership = OrganizationUser(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            is_active=True,
        )
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def get_membership(
        self,
        user_id: UUID,
        organization_id: int,
    ) -> OrganizationUser | None:
        """Получить членство пользователя в организации."""
        query = select(OrganizationUser).where(
            OrganizationUser.user_id == user_id,
            OrganizationUser.organization_id == organization_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def deactivate_membership(
        self,
        user_id: UUID,
        organization_id: int,
    ) -> None:
        """Деактивировать членство пользователя."""
        membership = await self.get_membership(user_id, organization_id)
        if membership:
            membership.is_active = False
            await self.session.flush()

    async def update_membership_role(
        self,
        user_id: UUID,
        organization_id: int,
        role: OrgRole,
    ) -> None:
        """Обновить роль пользователя в организации."""
        membership = await self.get_membership(user_id, organization_id)
        if membership:
            membership.role = role
            await self.session.flush()

    async def count_active_users(self, organization_id: int) -> int:
        """Подсчитать активных пользователей в организации."""
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

    async def get_users_by_ids(self, ids: Iterable[UUID]) -> list[User]:
        """Получить пользователей по списку ID."""
        query = select(User).where(User.id.in_(list(ids)))
        result = await self.session.execute(query)
        return list(result.scalars().all())
