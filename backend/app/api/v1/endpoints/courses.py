"""Эндпоинты LMS (курсы и назначения)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, Request, status

from app.core.dependencies import (
    ActiveSubscriptionContext,
    CurrentContext,
    DbSession,
    require_roles,
)
from app.models import OrgRole
from app.schemas.course import (
    CourseAssignmentResponse,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
)
from app.services.course_service import CourseService

router = APIRouter()


@router.get(
    "",
    response_model=list[CourseResponse],
    summary="Список курсов",
    description="Получение опубликованных курсов организации.",
)
async def list_courses(
    ctx: ActiveSubscriptionContext,
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CourseResponse]:
    service = CourseService(session)
    courses = await service.list_courses(ctx.organization_id, limit=limit, offset=offset)
    return [CourseResponse.model_validate(course) for course in courses]


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать курс",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def create_course(
    request: Request,
    data: CourseCreate,
    ctx: CurrentContext,
    session: DbSession,
) -> CourseResponse:
    service = CourseService(session)
    return await service.create_course(
        ctx.organization_id,
        data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Обновить курс",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def update_course(
    course_id: int,
    request: Request,
    data: CourseUpdate,
    ctx: CurrentContext,
    session: DbSession,
) -> CourseResponse:
    service = CourseService(session)
    return await service.update_course(
        course_id,
        ctx.organization_id,
        data,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{course_id}/publish",
    response_model=CourseResponse,
    summary="Публиковать курс",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def publish_course(
    course_id: int,
    request: Request,
    ctx: CurrentContext,
    session: DbSession,
) -> CourseResponse:
    service = CourseService(session)
    return await service.publish_course(
        course_id,
        ctx.organization_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{course_id}/assign",
    response_model=list[CourseAssignmentResponse],
    summary="Назначить курс пользователям",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def assign_course(
    course_id: int,
    request: Request,
    ctx: CurrentContext,
    session: DbSession,
    user_ids: Annotated[list[UUID], Body(embed=True, description="Список пользователей для назначения")],
) -> list[CourseAssignmentResponse]:
    service = CourseService(session)
    return await service.assign_course(
        course_id,
        ctx.organization_id,
        user_ids,
        actor_id=ctx.user.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{course_id}/progress",
    response_model=CourseAssignmentResponse,
    summary="Обновить прогресс курса для текущего пользователя",
)
async def update_progress(
    course_id: int,
    request: Request,
    ctx: ActiveSubscriptionContext,
    session: DbSession,
    progress_percent: Annotated[int, Query(ge=0, le=100)],
) -> CourseAssignmentResponse:
    service = CourseService(session)
    return await service.update_progress(
        course_id=course_id,
        organization_id=ctx.organization_id,
        user_id=ctx.user.id,
        progress_percent=progress_percent,
        request_id=getattr(request.state, "request_id", None) if request else None,
    )


@router.get(
    "/assignments/me",
    response_model=list[CourseAssignmentResponse],
    summary="Назначенные мне курсы",
)
async def my_assignments(
    ctx: ActiveSubscriptionContext,
    session: DbSession,
) -> list[CourseAssignmentResponse]:
    service = CourseService(session)
    return await service.list_assignments_for_user(
        user_id=ctx.user.id,
        organization_id=ctx.organization_id,
    )
