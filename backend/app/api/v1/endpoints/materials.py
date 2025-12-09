"""Эндпоинты базы знаний."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUser, DbSession
from app.models.material import MaterialType
from app.schemas.material import (
    MaterialListItem,
    MaterialListResponse,
    MaterialResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.material_service import MaterialService

router = APIRouter()


@router.get(
    "",
    response_model=MaterialListResponse,
    summary="Список материалов",
    description="Получение списка опубликованных материалов с пагинацией и фильтрацией.",
)
async def get_materials(
    session: DbSession,
    current_user: CurrentUser,
    type: MaterialType | None = Query(None, description="Фильтр по типу материала"),
    category_id: int | None = Query(None, description="Фильтр по категории"),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    page_size: int = Query(default=20, ge=1, le=100, description="Размер страницы"),
) -> MaterialListResponse:
    """Получить список материалов.

    - **type**: Тип материала (article, npa, template, reference, news)
    - **category_id**: ID категории
    - **page**: Номер страницы (начиная с 1)
    - **page_size**: Количество элементов на странице
    """
    service = MaterialService(session)
    return await service.get_materials(
        material_type=type,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Поиск материалов",
    description="Полнотекстовый поиск по базе знаний с ранжированием результатов.",
)
async def search_materials(
    session: DbSession,
    current_user: CurrentUser,
    q: str = Query(..., min_length=2, max_length=200, description="Поисковый запрос"),
    type: MaterialType | None = Query(None, description="Фильтр по типу"),
    category_id: int | None = Query(None, description="Фильтр по категории"),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    page_size: int = Query(default=20, ge=1, le=100, description="Размер страницы"),
) -> SearchResponse:
    """Поиск материалов по тексту.

    Использует полнотекстовый поиск PostgreSQL с поддержкой
    русской морфологии. Результаты ранжируются по релевантности.

    - **q**: Поисковый запрос (минимум 2 символа)
    - **type**: Фильтр по типу материала
    - **category_id**: Фильтр по категории
    - **page**: Номер страницы
    - **page_size**: Размер страницы
    """
    request = SearchRequest(
        query=q,
        type=type,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )
    service = MaterialService(session)
    return await service.search(request)


@router.get(
    "/popular",
    response_model=list[MaterialListItem],
    summary="Популярные материалы",
    description="Получение списка наиболее популярных материалов по количеству просмотров.",
)
async def get_popular_materials(
    session: DbSession,
    current_user: CurrentUser,
    type: MaterialType | None = Query(None, description="Фильтр по типу"),
    limit: int = Query(default=10, ge=1, le=50, description="Количество материалов"),
) -> list[MaterialListItem]:
    """Получить популярные материалы.

    - **type**: Тип материала для фильтрации
    - **limit**: Максимальное количество результатов
    """
    service = MaterialService(session)
    return await service.get_popular(material_type=type, limit=limit)


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="Получить материал",
    description="Получение полного содержимого материала по ID. "
    "Автоматически увеличивает счётчик просмотров.",
)
async def get_material(
    material_id: UUID,
    session: DbSession,
    current_user: CurrentUser,
) -> MaterialResponse:
    """Получить материал по ID.

    При каждом запросе увеличивается счётчик просмотров материала.
    """
    service = MaterialService(session)
    return await service.get_material(material_id)
