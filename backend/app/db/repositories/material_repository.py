"""Репозиторий для работы с материалами базы знаний."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.repositories.base import BaseRepository
from app.models import Material, MaterialStatus, MaterialType, MaterialVisibility


class MaterialRepository(BaseRepository[Material]):
    """Репозиторий для работы с материалами базы знаний."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Material, session)

    async def get_with_relations(self, material_id: UUID) -> Material | None:
        """Материал вместе с автором и организацией (для детального просмотра)."""
        query = (
            select(Material)
            .options(
                # joinedload для связей «к одному» подтягивает всё одним запросом
                # (LEFT JOIN), вместо отдельного запроса на каждую связь.
                joinedload(Material.author),
                joinedload(Material.organization),
                joinedload(Material.updated_by),
                joinedload(Material.news),
            )
            .where(Material.id == material_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

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
            Material.status == MaterialStatus.PUBLISHED,
            or_(
                Material.organization_id == organization_id,
                Material.visibility == MaterialVisibility.PUBLIC,
            ),
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

    async def list_by_status(
        self,
        *,
        organization_id: int,
        status: MaterialStatus,
        material_type: MaterialType | None = None,
        category_id: int | None = None,
        author_id: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Material], int]:
        """Материалы организации с заданным статусом (для черновиков и архива).

        Строго в пределах организации (без публичных из других орг). Если задан
        author_id — только материалы этого автора; иначе все авторы организации
        (используется для суперпользователя).
        """
        conditions = [
            Material.organization_id == organization_id,
            Material.status == status,
        ]
        if author_id is not None:
            conditions.append(Material.author_id == author_id)
        if material_type:
            conditions.append(Material.type == material_type)
        if category_id:
            conditions.append(Material.category_id == category_id)

        query = select(Material).where(*conditions)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        query = query.order_by(desc(Material.updated_at)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        materials = list(result.scalars().all())

        return materials, total

    async def search(
        self,
        query_str: str,
        *,
        organization_id: int,
        status: MaterialStatus | None = None,
        material_type: MaterialType | None = None,
        category_id: int | None = None,
        author_id: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Material], int]:
        """Полнотекстовый поиск материалов.

        По умолчанию (status пуст или published) ищет по опубликованным своей
        организации + публичным. Для черновиков/архива — строго внутри организации,
        и, если задан author_id, только материалы этого автора (приватность).
        """
        ts_query = func.plainto_tsquery("russian", query_str)

        rank = func.ts_rank(Material.search_vector, ts_query).label("rank")
        query = select(Material, rank).where(Material.search_vector.op("@@")(ts_query))

        if status is None or status == MaterialStatus.PUBLISHED:
            query = query.where(Material.status == MaterialStatus.PUBLISHED).where(
                or_(
                    Material.organization_id == organization_id,
                    Material.visibility == MaterialVisibility.PUBLIC,
                ),
            )
        else:
            query = query.where(
                Material.status == status,
                Material.organization_id == organization_id,
            )
            if author_id is not None:
                query = query.where(Material.author_id == author_id)

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
        """Увеличить счётчик просмотров материала.

        Явно сохраняем прежний updated_at, иначе onupdate сдвинул бы дату
        изменения при обычном просмотре (просмотр — не редактирование).
        """
        stmt = (
            update(Material)
            .where(Material.id == material_id)
            .values(views_count=Material.views_count + 1, updated_at=Material.updated_at)
        )
        await self.session.execute(stmt)

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
            .where(Material.status == MaterialStatus.PUBLISHED)
            .where(
                or_(
                    Material.organization_id == organization_id,
                    Material.visibility == MaterialVisibility.PUBLIC,
                ),
            )
            .order_by(desc(Material.views_count))
            .limit(limit)
        )

        if material_type:
            query = query.where(Material.type == material_type)

        result = await self.session.execute(query)
        return list(result.scalars().all())
