"""Репозиторий для работы с материалами базы знаний."""

from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.models import Material, MaterialType


class MaterialRepository(BaseRepository[Material]):
    """Репозиторий для работы с материалами базы знаний.

    Поддерживает полнотекстовый поиск через PostgreSQL FTS.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Material, session)

    async def get_published(
        self,
        *,
        material_type: MaterialType | None = None,
        category_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Material], int]:
        """Получить опубликованные материалы.

        Args:
            material_type: Фильтр по типу материала.
            category_id: Фильтр по категории.
            limit: Максимальное количество.
            offset: Смещение.

        Returns:
            Кортеж (список материалов, общее количество).
        """
        query = select(Material).where(Material.published_at.isnot(None))

        if material_type:
            query = query.where(Material.type == material_type)
        if category_id:
            query = query.where(Material.category_id == category_id)

        # Подсчёт общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        # Получение результатов с пагинацией
        query = query.order_by(desc(Material.published_at)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        materials = list(result.scalars().all())

        return materials, total

    async def search(
        self,
        query_str: str,
        *,
        material_type: MaterialType | None = None,
        category_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Material], int]:
        """Полнотекстовый поиск материалов.

        Использует PostgreSQL FTS с ранжированием результатов.

        Args:
            query_str: Поисковый запрос.
            material_type: Фильтр по типу.
            category_id: Фильтр по категории.
            limit: Максимальное количество.
            offset: Смещение.

        Returns:
            Кортеж (список материалов, общее количество).
        """
        # Преобразование запроса в tsquery
        ts_query = func.plainto_tsquery("russian", query_str)

        # Базовый запрос с ранжированием
        rank = func.ts_rank(Material.search_vector, ts_query).label("rank")
        query = (
            select(Material, rank)
            .where(Material.search_vector.op("@@")(ts_query))
            .where(Material.published_at.isnot(None))
        )

        # Фильтры
        if material_type:
            query = query.where(Material.type == material_type)
        if category_id:
            query = query.where(Material.category_id == category_id)

        # Подсчёт общего количества
        count_subquery = query.subquery()
        count_query = select(func.count()).select_from(count_subquery)
        total = await self.session.scalar(count_query) or 0

        # Результаты с пагинацией и сортировкой по релевантности
        query = query.order_by(desc("rank")).limit(limit).offset(offset)
        result = await self.session.execute(query)
        materials = [row[0] for row in result.all()]

        return materials, total

    async def get_with_documents(self, material_id: UUID) -> Material | None:
        """Получить материал с прикреплёнными документами.

        Args:
            material_id: ID материала.

        Returns:
            Материал с документами или None.
        """
        query = (
            select(Material)
            .where(Material.id == material_id)
            .options(selectinload(Material.documents))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def increment_views(self, material_id: UUID) -> None:
        """Увеличить счётчик просмотров материала.

        Args:
            material_id: ID материала.
        """
        material = await self.get_by_id(material_id)
        if material:
            material.views_count += 1
            await self.session.flush()

    async def get_popular(
        self,
        *,
        material_type: MaterialType | None = None,
        limit: int = 10,
    ) -> list[Material]:
        """Получить популярные материалы.

        Args:
            material_type: Фильтр по типу.
            limit: Максимальное количество.

        Returns:
            Список популярных материалов.
        """
        query = (
            select(Material)
            .where(Material.published_at.isnot(None))
            .order_by(desc(Material.views_count))
            .limit(limit)
        )

        if material_type:
            query = query.where(Material.type == material_type)

        result = await self.session.execute(query)
        return list(result.scalars().all())
