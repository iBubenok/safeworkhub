"""Репозиторий для работы с материалами базы знаний."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models import Material, MaterialStatus, MaterialType


class MaterialRepository(BaseRepository[Material]):
    """Репозиторий для работы с материалами базы знаний."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Material, session)

    async def get_published(
        self,
        *,
        organization_id: int,
        material_type: MaterialType | None = None,
        category_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Material], int]:
        """Получить опубликованные материалы."""
        query = select(Material).where(
            Material.organization_id == organization_id,
            Material.status == MaterialStatus.PUBLISHED,
        )

        if material_type:
            query = query.where(Material.type == material_type)
        if category_id:
            query = query.where(Material.category_id == category_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        query = query.order_by(desc(Material.published_at)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        materials = list(result.scalars().all())

        return materials, total

    async def search(
        self,
        query_str: str,
        *,
        organization_id: int,
        material_type: MaterialType | None = None,
        category_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Material], int]:
        """Полнотекстовый поиск материалов."""
        ts_query = func.plainto_tsquery("russian", query_str)

        rank = func.ts_rank(Material.search_vector, ts_query).label("rank")
        query = (
            select(Material, rank)
            .where(Material.search_vector.op("@@")(ts_query))
            .where(
                Material.organization_id == organization_id,
                Material.status == MaterialStatus.PUBLISHED,
            )
        )

        if material_type:
            query = query.where(Material.type == material_type)
        if category_id:
            query = query.where(Material.category_id == category_id)

        count_subquery = query.subquery()
        count_query = select(func.count()).select_from(count_subquery)
        total = await self.session.scalar(count_query) or 0

        query = query.order_by(desc("rank")).limit(limit).offset(offset)
        result = await self.session.execute(query)
        materials = [row[0] for row in result.all()]

        return materials, total

    async def increment_views(self, material_id: UUID) -> None:
        """Увеличить счётчик просмотров материала."""
        material = await self.get_by_id(material_id)
        if material:
            material.views_count += 1
            await self.session.flush()

    async def get_popular(
        self,
        *,
        organization_id: int,
        material_type: MaterialType | None = None,
        limit: int = 10,
    ) -> list[Material]:
        """Получить популярные материалы."""
        query = (
            select(Material)
            .where(
                Material.organization_id == organization_id,
                Material.status == MaterialStatus.PUBLISHED,
            )
            .order_by(desc(Material.views_count))
            .limit(limit)
        )

        if material_type:
            query = query.where(Material.type == material_type)

        result = await self.session.execute(query)
        return list(result.scalars().all())
