"""Эндпоинты аутентификации."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DbSession
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему",
    description="Аутентификация пользователя по email и паролю. "
    "Возвращает JWT токены для доступа к API.",
)
async def login(
    data: LoginRequest,
    session: DbSession,
) -> TokenResponse:
    """Аутентификация пользователя.

    - **email**: Email пользователя
    - **password**: Пароль пользователя
    """
    service = AuthService(session)
    return await service.login(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновление токенов",
    description="Обновление access и refresh токенов по действующему refresh токену.",
)
async def refresh_tokens(
    data: RefreshTokenRequest,
    session: DbSession,
) -> TokenResponse:
    """Обновление токенов.

    - **refresh_token**: Действующий refresh token
    """
    service = AuthService(session)
    return await service.refresh_tokens(data.refresh_token)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация организации",
    description="Регистрация новой организации с созданием учётной записи администратора. "
    "Автоматически активируется 14-дневный пробный период.",
)
async def register(
    data: RegisterRequest,
    session: DbSession,
) -> RegisterResponse:
    """Регистрация новой организации.

    - **organization_name**: Название организации
    - **inn**: ИНН организации (10 или 12 цифр)
    - **admin_email**: Email администратора
    - **admin_password**: Пароль администратора (минимум 8 символов)
    - **admin_name**: Имя администратора
    """
    service = AuthService(session)
    return await service.register(data)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
    description="Инвалидация текущей сессии. "
    "На стороне клиента необходимо удалить сохранённые токены.",
)
async def logout() -> None:
    """Выход из системы.

    Токены на стороне сервера не хранятся (stateless JWT),
    поэтому клиент должен самостоятельно удалить токены.
    """
    # В stateless JWT logout обрабатывается на клиенте
    # При необходимости можно добавить blacklist токенов в Redis
    pass
