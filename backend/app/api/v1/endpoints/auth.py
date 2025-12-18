"""Эндпоинты аутентификации."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
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
bearer = HTTPBearer(auto_error=False)


def set_refresh_cookie(response: Response, refresh_token: str | None) -> None:
    """Установить httpOnly cookie с refresh токеном."""
    if not refresh_token:
        return

    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_token_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        domain=settings.refresh_token_domain,
        path=settings.refresh_cookie_path,
    )


def clear_refresh_cookie(response: Response) -> None:
    """Удалить refresh cookie у клиента."""
    response.delete_cookie(
        settings.refresh_token_cookie_name,
        path=settings.refresh_cookie_path,
        domain=settings.refresh_token_domain,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему",
    description=(
        "Аутентификация пользователя по email и паролю. "
        "Возвращает новый access token и устанавливает refresh token в httpOnly cookie."
    ),
)
async def login(
    request: Request,
    data: LoginRequest,
    response: Response,
    session: DbSession,
) -> TokenResponse:
    service = AuthService(session)
    tokens = await service.login(
        data,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )
    set_refresh_cookie(response, tokens.refresh_token)
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновление токенов",
    description="Обновление пары токенов по действующему refresh токену.",
)
async def refresh_tokens(
    request: Request,
    response: Response,
    session: DbSession,
    body: Annotated[RefreshTokenRequest | None, Body()] = None,
) -> TokenResponse:
    refresh_token = (
        body.refresh_token if body else None
    ) or request.cookies.get(settings.refresh_token_cookie_name)
    service = AuthService(session)
    tokens = await service.refresh_tokens(
        refresh_token=refresh_token or "",
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )
    set_refresh_cookie(response, tokens.refresh_token)
    return tokens


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация организации",
    description="Регистрация новой организации с созданием учётной записи владельца.",
)
async def register(
    data: RegisterRequest,
    session: DbSession,
) -> RegisterResponse:
    service = AuthService(session)
    return await service.register(data)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
    description="Отзывает refresh-сессию и удаляет cookie на клиенте.",
)
async def logout(
    request: Request,
    response: Response,
    session: DbSession,
    _credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)] = None,
) -> None:
    token = request.cookies.get(settings.refresh_token_cookie_name)
    service = AuthService(session)
    await service.logout(token)
    clear_refresh_cookie(response)
