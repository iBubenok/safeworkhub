"""Репозиторий категорий материалов."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models import Category


class CategoryRepository(BaseRepository[Category]):
    """Работа с категориями материалов."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Category, session)

    async def list_by_organization(self, organization_id: int) -> list[Category]:
        query = select(Category).where(Category.organization_id == organization_id).order_by(
            Category.sort_order, Category.name
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_slug(self, organization_id: int, slug: str) -> Category | None:
        query = select(Category).where(
            Category.organization_id == organization_id,
            Category.slug == slug,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
