"""FastAPI зависимости для внедрения в эндпоинты."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import TokenType, verify_token
from app.db.repositories import SubscriptionRepository, UserRepository
from app.db.session import get_session
from app.models import OrgRole, SubscriptionStatus, User
from app.services.notification_service import NotificationService
from app.services.redis_service import RedisService

security = HTTPBearer(auto_error=False)


@dataclass
class RequestContext:
    """Контекст запроса с данными пользователя и организации."""

    user: User
    organization_id: int
    role: OrgRole


async def _extract_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        raise AuthenticationError("Требуется аутентификация")
    return credentials.credentials


async def _resolve_context(
    token: str,
    session: AsyncSession,
    request: Request | None = None,
) -> RequestContext:
    """Собрать контекст пользователя из access-токена."""
    payload = verify_token(token, TokenType.ACCESS)
    if payload is None or payload.org is None:
        raise AuthenticationError("Невалидный токен")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(payload.sub)
    if user is None or not user.is_active:
        raise AuthenticationError("Пользователь не найден")

    membership = await user_repo.get_membership(user.id, payload.org)
    if membership is None or not membership.is_active:
        raise AuthorizationError("Нет доступа к организации")

    if request is not None:
        request.state.organization_id = payload.org
        request.state.user_id = str(user.id)

    return RequestContext(
        user=user,
        organization_id=payload.org,
        role=membership.role if isinstance(membership.role, OrgRole) else OrgRole(membership.role),
    )


async def get_current_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequestContext:
    """Получить контекст аутентифицированного пользователя."""
    token = await _extract_token(credentials)
    return await _resolve_context(token, session, request)


async def get_current_context_from_token(
    token: Annotated[str, Query(min_length=1)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequestContext:
    """Получить контекст аутентифицированного пользователя из query token."""
    return await _resolve_context(token, session)


async def get_redis() -> AsyncGenerator[Redis, None]:
    """Получить Redis-клиент на время запроса."""
    redis_client = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield redis_client
    finally:
        await redis_client.aclose()


async def get_redis_service(
    redis_client: Annotated[Redis, Depends(get_redis)],
) -> RedisService:
    """Собрать сервис Redis поверх клиента."""
    return RedisService(redis_client)


async def get_notification_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    redis_service: Annotated[RedisService, Depends(get_redis_service)],
) -> NotificationService:
    """Собрать сервис уведомлений через DI FastAPI."""
    return NotificationService(session, redis_service)


def require_roles(*allowed_roles: OrgRole) -> Callable[[RequestContext], Awaitable[RequestContext]]:
    """Создать dependency для проверки ролей."""

    async def checker(
        ctx: Annotated[RequestContext, Depends(get_current_context)],
    ) -> RequestContext:
        if ctx.user.is_superuser:
            return ctx
        if ctx.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return ctx

    return checker


async def enforce_active_subscription(
    ctx: Annotated[RequestContext, Depends(get_current_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequestContext:
    """Проверить активность подписки организации."""
    subscription_repo = SubscriptionRepository(session)
    subscription = await subscription_repo.get_with_tariff(ctx.organization_id)
    if subscription is None or subscription.status not in {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE}:
        raise AuthorizationError("Подписка неактивна")
    return ctx


CurrentContext = Annotated[RequestContext, Depends(get_current_context)]
CurrentContextFromToken = Annotated[RequestContext, Depends(get_current_context_from_token)]
ActiveSubscriptionContext = Annotated[RequestContext, Depends(enforce_active_subscription)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
CurrentNotificationService = Annotated[NotificationService, Depends(get_notification_service)]
RedisSession = Annotated[RedisService, Depends(get_redis)]
