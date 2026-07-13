"""Эндпоинты для работы с пользователями."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import CurrentContext, DbSession, require_roles
from app.models import OrgRole
from app.schemas.user import (
    OrgMemberOption,
    PasswordChangeSelf,
    PasswordSet,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserWithMemberships,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=UserWithMemberships,
    summary="Текущий пользователь",
    description="Получение информации о текущем аутентифицированном пользователе.",
)
async def get_current_user(
    ctx: CurrentContext,
    session: DbSession,
) -> UserWithMemberships:
    service = UserService(session)
    return await service.get_user(ctx.user.id)


@router.patch(
    "/me",
    response_model=UserWithMemberships,
    summary="Обновление профиля",
    description="Обновление данных текущего пользователя.",
)
async def update_current_user(
    data: UserUpdate,
    ctx: CurrentContext,
    session: DbSession,
) -> UserWithMemberships:
    service = UserService(session)
    return await service.update_user(ctx.user.id, ctx.organization_id, data)


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Сменить свой пароль",
    description="Смена собственного пароля с подтверждением текущего. Доступно любому пользователю.",
)
async def change_own_password(
    request: Request,
    data: PasswordChangeSelf,
    ctx: CurrentContext,
    session: DbSession,
) -> None:
    service = UserService(session)
    await service.change_own_password(
        ctx.user.id,
        organization_id=ctx.organization_id,
        current_password=data.current_password,
        new_password=data.new_password,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Задать пароль пользователю",
    description=(
        "Установка нового пароля другому пользователю. Суперпользователь — любому в организации, "
        "владелец — только сотрудникам."
    ),
)
async def set_user_password(
    user_id: UUID,
    request: Request,
    data: PasswordSet,
    ctx: CurrentContext,
    session: DbSession,
) -> None:
    service = UserService(session)
    await service.set_user_password(
        user_id,
        organization_id=ctx.organization_id,
        actor_id=ctx.user.id,
        actor_role=ctx.role,
        actor_is_superuser=ctx.user.is_superuser,
        new_password=data.new_password,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/members",
    response_model=list[OrgMemberOption],
    summary="Участники организации",
    description="Краткий список активных участников организации. Доступно любому участнику (для назначений).",
)
async def list_members(
    ctx: CurrentContext,
    session: DbSession,
) -> list[OrgMemberOption]:
    service = UserService(session)
    return await service.list_org_members(ctx.organization_id)


@router.get(
    "/{user_id}",
    response_model=UserWithMemberships,
    summary="Получить пользователя",
    description=(
        "Получение информации о пользователе по ID. Требуются права владельца организации или администратора платформы."
    ),
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def get_user(
    user_id: UUID,
    session: DbSession,
) -> UserWithMemberships:
    service = UserService(session)
    return await service.get_user(user_id)


@router.post(
    "",
    response_model=UserWithMemberships,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    description=("Создание нового пользователя в организации. Требуются права владельца организации."),
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def create_user(
    request: Request,
    data: UserCreate,
    ctx: CurrentContext,
    session: DbSession,
) -> UserWithMemberships:
    service = UserService(session)
    return await service.create_user(
        data,
        organization_id=ctx.organization_id,
        actor_id=ctx.user.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/{user_id}",
    response_model=UserWithMemberships,
    summary="Обновить пользователя",
    description="Обновление данных пользователя. Требуются права владельца организации.",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    ctx: CurrentContext,
    session: DbSession,
) -> UserWithMemberships:
    service = UserService(session)
    return await service.update_user(user_id, ctx.organization_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Деактивировать пользователя",
    description=("Деактивация пользователя (мягкое удаление). Требуются права владельца организации."),
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def deactivate_user(
    user_id: UUID,
    request: Request,
    ctx: CurrentContext,
    session: DbSession,
) -> None:
    service = UserService(session)
    await service.deactivate_user(
        user_id,
        ctx.organization_id,
        actor_id=ctx.user.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{user_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Активировать пользователя",
    description="Восстановление ранее деактивированного пользователя. Требуются права владельца организации.",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def activate_user(
    user_id: UUID,
    request: Request,
    ctx: CurrentContext,
    session: DbSession,
) -> None:
    service = UserService(session)
    await service.activate_user(
        user_id,
        ctx.organization_id,
        actor_id=ctx.user.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Поиск пользователей",
    description="Поиск пользователей организации. Требуются права владельца организации.",
    dependencies=[Depends(require_roles(OrgRole.ORG_OWNER))],
)
async def search_users(
    ctx: CurrentContext,
    session: DbSession,
    q: Annotated[str, Query(description="Поисковый запрос")] = "",
    limit: Annotated[int, Query(ge=1, le=100, description="Максимум результатов")] = 20,
    offset: Annotated[int, Query(ge=0, description="Смещение")] = 0,
) -> list[UserResponse]:
    service = UserService(session)
    return await service.search_users(ctx.organization_id, q, limit=limit, offset=offset)
