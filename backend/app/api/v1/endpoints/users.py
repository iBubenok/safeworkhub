"""Эндпоинты для работы с пользователями."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, CurrentSuperuser, DbSession
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Текущий пользователь",
    description="Получение информации о текущем аутентифицированном пользователе.",
)
async def get_current_user(
    current_user: CurrentUser,
) -> UserResponse:
    """Получить данные текущего пользователя."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Обновление профиля",
    description="Обновление данных текущего пользователя.",
)
async def update_current_user(
    data: UserUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> UserResponse:
    """Обновить данные текущего пользователя.

    - **name**: Новое имя (опционально)
    - **email**: Новый email (опционально)
    """
    service = UserService(session)
    return await service.update_user(current_user.id, data)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получить пользователя",
    description="Получение информации о пользователе по ID. "
    "Требуются права администратора.",
)
async def get_user(
    user_id: UUID,
    session: DbSession,
    current_user: CurrentSuperuser,
) -> UserResponse:
    """Получить пользователя по ID.

    Доступно только администраторам.
    """
    service = UserService(session)
    return await service.get_user(user_id)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    description="Создание нового пользователя. Требуются права администратора.",
)
async def create_user(
    data: UserCreate,
    session: DbSession,
    current_user: CurrentSuperuser,
) -> UserResponse:
    """Создать нового пользователя.

    Доступно только администраторам.

    - **email**: Email нового пользователя
    - **password**: Пароль (минимум 8 символов)
    - **name**: Имя пользователя
    """
    service = UserService(session)
    return await service.create_user(data)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Обновить пользователя",
    description="Обновление данных пользователя. Требуются права администратора.",
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    session: DbSession,
    current_user: CurrentSuperuser,
) -> UserResponse:
    """Обновить данные пользователя.

    Доступно только администраторам.
    """
    service = UserService(session)
    return await service.update_user(user_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Деактивировать пользователя",
    description="Деактивация пользователя (мягкое удаление). "
    "Требуются права администратора.",
)
async def deactivate_user(
    user_id: UUID,
    session: DbSession,
    current_user: CurrentSuperuser,
) -> None:
    """Деактивировать пользователя.

    Пользователь не удаляется физически, а помечается как неактивный.
    Доступно только администраторам.
    """
    service = UserService(session)
    await service.deactivate_user(user_id)


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Поиск пользователей",
    description="Поиск пользователей по email или имени. "
    "Требуются права администратора.",
)
async def search_users(
    session: DbSession,
    current_user: CurrentSuperuser,
    q: str = Query(default="", description="Поисковый запрос"),
    limit: int = Query(default=20, ge=1, le=100, description="Максимум результатов"),
    offset: int = Query(default=0, ge=0, description="Смещение"),
) -> list[UserResponse]:
    """Поиск пользователей.

    Доступно только администраторам.

    - **q**: Строка поиска (по email или имени)
    - **limit**: Максимальное количество результатов
    - **offset**: Смещение от начала
    """
    service = UserService(session)
    return await service.search_users(q, limit=limit, offset=offset)
