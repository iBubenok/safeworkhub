"""Эндпоинты подмодуля «Проверки» (проведение проверки по чек-листу)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, status

from app.core.dependencies import ActiveSubscriptionContext, CurrentContext, DbSession
from app.models import OrgRole
from app.models.checklist_run import ChecklistRunStatus
from app.schemas.checklist_run import (
    ChecklistRunAssigneesUpdate,
    ChecklistRunCreate,
    ChecklistRunListResponse,
    ChecklistRunResponse,
    ChecklistRunUpdate,
)
from app.services.checklist_run_service import ChecklistRunService

router = APIRouter()


def _is_owner(ctx: ActiveSubscriptionContext) -> bool:
    return ctx.role == OrgRole.ORG_OWNER or ctx.user.is_superuser


@router.post(
    "",
    response_model=ChecklistRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Начать проверку",
    description="Создаёт проверку по опубликованному чек-листу. Доступно любому участнику организации.",
)
async def start_run(
    request: Request,
    data: ChecklistRunCreate,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistRunResponse:
    service = ChecklistRunService(session)
    return await service.start_run(
        organization_id=ctx.organization_id,
        conducted_by_id=ctx.user.id,
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "",
    response_model=ChecklistRunListResponse,
    summary="Список проверок",
    description="Проверки организации. Видны всем участникам организации.",
)
async def list_runs(
    ctx: CurrentContext,
    session: DbSession,
    status_filter: Annotated[ChecklistRunStatus | None, Query(alias="status", description="Фильтр по статусу")] = None,
    q: Annotated[str, Query(description="Поиск по названию проверки/чек-листа")] = "",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ChecklistRunListResponse:
    service = ChecklistRunService(session)
    return await service.list_runs(
        organization_id=ctx.organization_id,
        status=status_filter,
        search=q.strip() or None,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{run_id}",
    response_model=ChecklistRunResponse,
    summary="Получить проверку",
    description="Полная проверка с ответами по пунктам.",
)
async def get_run(
    run_id: UUID,
    ctx: CurrentContext,
    session: DbSession,
) -> ChecklistRunResponse:
    service = ChecklistRunService(session)
    return await service.get_run(run_id, organization_id=ctx.organization_id)


@router.patch(
    "/{run_id}",
    response_model=ChecklistRunResponse,
    summary="Сохранить ход проверки",
    description="Обновление ответов/комментариев. Доступно проводящему проверку или владельцу, пока она не завершена.",
)
async def update_run(
    run_id: UUID,
    request: Request,
    data: ChecklistRunUpdate,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistRunResponse:
    service = ChecklistRunService(session)
    return await service.update_run(
        run_id,
        organization_id=ctx.organization_id,
        editor_id=ctx.user.id,
        is_owner=_is_owner(ctx),
        data=data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.put(
    "/{run_id}/assignees",
    response_model=ChecklistRunResponse,
    summary="Изменить состав назначенных",
    description="Заменяет список назначенных сотрудников. Доступно создателю проверки или владельцу организации.",
)
async def set_assignees(
    run_id: UUID,
    request: Request,
    data: ChecklistRunAssigneesUpdate,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistRunResponse:
    service = ChecklistRunService(session)
    return await service.set_assignees(
        run_id,
        organization_id=ctx.organization_id,
        actor_id=ctx.user.id,
        is_owner=_is_owner(ctx),
        assignee_ids=data.assignee_ids,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{run_id}/reopen",
    response_model=ChecklistRunResponse,
    summary="Возобновить проверку для корректировок",
    description="Возвращает завершённую проверку в статус «В процессе». Доступно исполнителю или владельцу.",
)
async def reopen_run(
    run_id: UUID,
    request: Request,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistRunResponse:
    service = ChecklistRunService(session)
    return await service.reopen_run(
        run_id,
        organization_id=ctx.organization_id,
        editor_id=ctx.user.id,
        is_owner=_is_owner(ctx),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{run_id}/complete",
    response_model=ChecklistRunResponse,
    summary="Завершить проверку",
    description="Финализирует проверку и считает итог. После завершения проверка только для чтения.",
)
async def complete_run(
    run_id: UUID,
    request: Request,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> ChecklistRunResponse:
    service = ChecklistRunService(session)
    return await service.complete_run(
        run_id,
        organization_id=ctx.organization_id,
        editor_id=ctx.user.id,
        is_owner=_is_owner(ctx),
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete(
    "/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить проверку",
    description="Удаление проверки. Доступно проводящему её или владельцу организации.",
)
async def delete_run(
    run_id: UUID,
    request: Request,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> None:
    service = ChecklistRunService(session)
    await service.delete_run(
        run_id,
        organization_id=ctx.organization_id,
        user_id=ctx.user.id,
        is_owner=_is_owner(ctx),
        request_id=getattr(request.state, "request_id", None),
    )
