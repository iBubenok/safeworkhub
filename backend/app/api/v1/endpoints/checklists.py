"""Эндпоинты подмодуля «Чек-листы»."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import (
    ActiveSubscriptionContext,
    CurrentContext,
    DbSession,
    require_roles,
)
from app.models import OrgRole
from app.models.checklist import ChecklistStatus
from app.schemas.checklist import (
    ChecklistCreate,
    ChecklistListResponse,
    ChecklistResponse,
    ChecklistUpdate,
)
from app.services.checklist_service import ChecklistService

router = APIRouter()


def _is_owner(ctx: CurrentContext | ActiveSubscriptionContext) -> bool:
    return ctx.role == OrgRole.ORG_OWNER or ctx.user.is_superuser


@router.get(
    "",
    response_model=ChecklistListResponse,
    summary="Список чек-листов",
    description="Чек-листы организации. Обычный пользователь видит только опубликованные.",
)
async def list_checklists(
    ctx: CurrentContext,
    session: DbSession,
    status_filter: Annotated[ChecklistStatus | None, Query(alias="status", description="Фильтр по статусу")] = None,
    q: Annotated[str, Query(description="Поиск по названию/описанию")] = "",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ChecklistListResponse:
    service = ChecklistService(session)
    return await service.list_checklists(
        organization_id=ctx.organization_id,
        is_owner=_is_owner(ctx),
        status=status_filter,
        search=q.strip() or None,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=ChecklistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать чек-лист",
    description="Создание чек-листа через конструктор. Требуются права владельца организации.",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def create_checklist(
    request: Request,
    data: ChecklistCreate,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistResponse:
    service = ChecklistService(session)
    return await service.create_checklist(
        organization_id=ctx.organization_id,
        author_id=ctx.user.id,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/{checklist_id}",
    response_model=ChecklistResponse,
    summary="Получить чек-лист",
    description="Полный чек-лист с пунктами.",
)
async def get_checklist(
    checklist_id: UUID,
    ctx: CurrentContext,
    session: DbSession,
) -> ChecklistResponse:
    service = ChecklistService(session)
    return await service.get_checklist(
        checklist_id,
        organization_id=ctx.organization_id,
        is_owner=_is_owner(ctx),
    )


@router.patch(
    "/{checklist_id}",
    response_model=ChecklistResponse,
    summary="Обновить чек-лист",
    description="Редактирование чек-листа. Требуются права владельца организации.",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def update_checklist(
    checklist_id: UUID,
    request: Request,
    data: ChecklistUpdate,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistResponse:
    service = ChecklistService(session)
    return await service.update_checklist(
        checklist_id,
        organization_id=ctx.organization_id,
        editor_id=ctx.user.id,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{checklist_id}/publish",
    response_model=ChecklistResponse,
    summary="Опубликовать чек-лист",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def publish_checklist(
    checklist_id: UUID,
    request: Request,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistResponse:
    service = ChecklistService(session)
    return await service.publish_checklist(
        checklist_id,
        organization_id=ctx.organization_id,
        editor_id=ctx.user.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{checklist_id}/archive",
    response_model=ChecklistResponse,
    summary="Архивировать чек-лист",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def archive_checklist(
    checklist_id: UUID,
    request: Request,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistResponse:
    service = ChecklistService(session)
    return await service.archive_checklist(
        checklist_id,
        organization_id=ctx.organization_id,
        editor_id=ctx.user.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete(
    "/{checklist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить чек-лист",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def delete_checklist(
    checklist_id: UUID,
    request: Request,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> None:
    service = ChecklistService(session)
    await service.delete_checklist(
        checklist_id,
        organization_id=ctx.organization_id,
        user_id=ctx.user.id,
        request_id=getattr(request.state, "request_id", None),
    )
