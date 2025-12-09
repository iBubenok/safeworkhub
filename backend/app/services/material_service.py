"""Сервис для работы с материалами базы знаний."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.repositories import MaterialRepository
from app.models.material import MaterialType
from app.schemas.material import (
    MaterialListItem,
    MaterialListResponse,
    MaterialResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)


class MaterialService:
    """Сервис для работы с материалами базы знаний.

    Предоставляет методы для поиска, просмотра и управления материалами.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = MaterialRepository(session)

    async def get_material(self, material_id: UUID) -> MaterialResponse:
        """Получить материал по ID.

        При каждом просмотре увеличивается счётчик просмотров.

        Args:
            material_id: ID материала.

        Returns:
            Данные материала.

        Raises:
            NotFoundError: Материал не найден.
        """
        material = await self.repository.get_by_id(material_id)
        if material is None or not material.is_published:
            raise NotFoundError("Материал", str(material_id))

        # Увеличиваем счётчик просмотров
        await self.repository.increment_views(material_id)

        return MaterialResponse.model_validate(material)

    async def get_materials(
        self,
        *,
        material_type: MaterialType | None = None,
        category_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> MaterialListResponse:
        """Получить список материалов с пагинацией.

        Args:
            material_type: Фильтр по типу материала.
            category_id: Фильтр по категории.
            page: Номер страницы.
            page_size: Размер страницы.

        Returns:
            Список материалов с информацией о пагинации.
        """
        offset = (page - 1) * page_size

        materials, total = await self.repository.get_published(
            material_type=material_type,
            category_id=category_id,
            limit=page_size,
            offset=offset,
        )

        items = [MaterialListItem.model_validate(m) for m in materials]
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return MaterialListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Полнотекстовый поиск материалов.

        Args:
            request: Параметры поиска.

        Returns:
            Результаты поиска с пагинацией.
        """
        offset = (request.page - 1) * request.page_size

        materials, total = await self.repository.search(
            request.query,
            material_type=request.type,
            category_id=request.category_id,
            limit=request.page_size,
            offset=offset,
        )

        items = [
            SearchResult(
                id=m.id,
                title=m.title,
                summary=m.summary,
                type=m.type,
                views_count=m.views_count,
                published_at=m.published_at,
                highlights=None,  # Можно добавить подсветку позже
            )
            for m in materials
        ]

        pages = (total + request.page_size - 1) // request.page_size if request.page_size > 0 else 0

        return SearchResponse(
            items=items,
            total=total,
            query=request.query,
            page=request.page,
            page_size=request.page_size,
            pages=pages,
        )

    async def get_popular(
        self,
        material_type: MaterialType | None = None,
        limit: int = 10,
    ) -> list[MaterialListItem]:
        """Получить популярные материалы.

        Args:
            material_type: Фильтр по типу.
            limit: Максимальное количество.

        Returns:
            Список популярных материалов.
        """
        materials = await self.repository.get_popular(
            material_type=material_type,
            limit=limit,
        )
        return [MaterialListItem.model_validate(m) for m in materials]
