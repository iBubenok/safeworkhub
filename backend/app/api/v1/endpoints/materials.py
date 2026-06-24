"""Эндпоинты базы знаний."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import (
    ActiveSubscriptionContext,
    CurrentContext,
    DbSession,
    require_roles,
)
from app.models.material import MaterialStatus, MaterialType
from app.models.organization import OrgRole
from app.schemas.material import (
    ArticleCreate,
    CategoryCreate,
    CategoryResponse,
    MaterialCreate,
    MaterialListItem,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
    SearchRequest,
    SearchResponse,
)
from app.services.material_service import MaterialService

router = APIRouter()


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="Список категорий",
    description="Получение списка категорий организации.",
)
async def list_categories(
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> list[CategoryResponse]:
    service = MaterialService(session)
    categories = await service.list_categories(ctx.organization_id)
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать категорию",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def create_category(
    request: Request,
    data: CategoryCreate,
    ctx: CurrentContext,
    session: DbSession,
) -> CategoryResponse:
    service = MaterialService(session)
    category = await service.create_category(
        ctx.organization_id,
        data,
        request_id=getattr(request.state, "request_id", None),
    )
    return CategoryResponse.model_validate(category)


@router.post(
    "",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать материал",
    description="Создание материала базы знаний. Требуются права владельца организации.",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def create_material(
    request: Request,
    data: MaterialCreate,
    ctx: CurrentContext,
    session: DbSession,
) -> MaterialResponse:
    service = MaterialService(session)
    return await service.create_material(
        organization_id=ctx.organization_id,
        author_id=ctx.user.id,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/articles",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать статью",
    description="Создание материала типа «статья» (Markdown). Требуются права владельца организации.",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def create_article(
    request: Request,
    data: ArticleCreate,
    ctx: CurrentContext,
    session: DbSession,
) -> MaterialResponse:
    service = MaterialService(session)
    return await service.create_article(
        organization_id=ctx.organization_id,
        author_id=ctx.user.id,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="Обновить материал",
    description="Редактирование материала. Доступно только автору материала.",
)
async def update_material(
    material_id: UUID,
    request: Request,
    data: MaterialUpdate,
    ctx: CurrentContext,
    session: DbSession,
) -> MaterialResponse:
    service = MaterialService(session)
    return await service.update_material(
        material_id,
        organization_id=ctx.organization_id,
        editor_id=ctx.user.id,
        data=data,
        is_superuser=ctx.user.is_superuser,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{material_id}/publish",
    response_model=MaterialResponse,
    summary="Публикация материала",
    description="Перевод материала в статус опубликованного.",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def publish_material(
    material_id: UUID,
    request: Request,
    ctx: CurrentContext,
    session: DbSession,
) -> MaterialResponse:
    service = MaterialService(session)
    return await service.publish(
        material_id,
        organization_id=ctx.organization_id,
        editor_id=ctx.user.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "",
    response_model=MaterialListResponse,
    summary="Список материалов",
    description="Получение списка опубликованных материалов с пагинацией и фильтрацией.",
)
async def get_materials(
    ctx: ActiveSubscriptionContext,
    session: DbSession,
    material_type: Annotated[MaterialType | None, Query(description="Фильтр по типу материала", alias="type")] = None,
    category_id: Annotated[int | None, Query(description="Фильтр по категории")] = None,
    status: Annotated[
        MaterialStatus | None,
        Query(description="Фильтр по статусу: published (по умолчанию), draft, archived"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Номер страницы")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Размер страницы")] = 20,
) -> MaterialListResponse:
    service = MaterialService(session)
    return await service.get_materials(
        organization_id=ctx.organization_id,
        material_type=material_type,
        category_id=category_id,
        status=status,
        requester_id=ctx.user.id,
        is_superuser=ctx.user.is_superuser,
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
    ctx: ActiveSubscriptionContext,
    session: DbSession,
    q: Annotated[str, Query(min_length=2, max_length=200, description="Поисковый запрос")],
    material_type: Annotated[MaterialType | None, Query(description="Фильтр по типу", alias="type")] = None,
    category_id: Annotated[int | None, Query(description="Фильтр по категории")] = None,
    page: Annotated[int, Query(ge=1, description="Номер страницы")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Размер страницы")] = 20,
) -> SearchResponse:
    request = SearchRequest(
        query=q,
        type=material_type,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )
    service = MaterialService(session)
    return await service.search(request, organization_id=ctx.organization_id)


@router.get(
    "/popular",
    response_model=list[MaterialListItem],
    summary="Популярные материалы",
    description="Получение списка наиболее популярных материалов по количеству просмотров.",
)
async def get_popular_materials(
    ctx: ActiveSubscriptionContext,
    session: DbSession,
    material_type: Annotated[MaterialType | None, Query(description="Фильтр по типу", alias="type")] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Количество материалов")] = 10,
) -> list[MaterialListItem]:
    service = MaterialService(session)
    return await service.get_popular(
        organization_id=ctx.organization_id,
        material_type=material_type,
        limit=limit,
    )


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="Получить материал",
    description="Получение полного содержимого материала по ID. Автоматически увеличивает счётчик просмотров.",
)
async def get_material(
    material_id: UUID,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> MaterialResponse:
    service = MaterialService(session)
    return await service.get_material(
        material_id,
        organization_id=ctx.organization_id,
        requester_id=ctx.user.id,
        is_superuser=ctx.user.is_superuser,
    )


@router.post(
    "/{material_id}/archive",
    response_model=MaterialResponse,
    summary="Архивировать материал",
    description="Перевод материала в архив. Доступно только автору материала.",
)
async def archive_material(
    material_id: UUID,
    request: Request,
    ctx: CurrentContext,
    session: DbSession,
) -> MaterialResponse:
    service = MaterialService(session)
    return await service.archive_material(
        material_id,
        organization_id=ctx.organization_id,
        user_id=ctx.user.id,
        is_superuser=ctx.user.is_superuser,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить материал",
    description="Полное удаление материала. Доступно только автору материала.",
)
async def delete_material(
    material_id: UUID,
    request: Request,
    ctx: CurrentContext,
    session: DbSession,
) -> None:
    service = MaterialService(session)
    await service.delete_material(
        material_id,
        organization_id=ctx.organization_id,
        user_id=ctx.user.id,
        is_superuser=ctx.user.is_superuser,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{material_id}/restore",
    response_model=MaterialResponse,
    summary="Восстановить материал из архива",
    description="Возврат материала из архива в черновик. Доступно только автору материала.",
)
async def restore_material(
    material_id: UUID,
    request: Request,
    ctx: CurrentContext,
    session: DbSession,
) -> MaterialResponse:
    service = MaterialService(session)
    return await service.restore_material(
        material_id,
        organization_id=ctx.organization_id,
        user_id=ctx.user.id,
        is_superuser=ctx.user.is_superuser,
        request_id=getattr(request.state, "request_id", None),
    )
