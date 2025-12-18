"""FastAPI зависимости для внедрения в эндпоинты."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import TokenType, verify_token
from app.db.repositories import SubscriptionRepository, UserRepository
from app.db.session import get_session
from app.models import OrgRole, SubscriptionStatus, User

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


async def get_current_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequestContext:
    """Получить контекст аутентифицированного пользователя."""
    token = await _extract_token(credentials)
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

    request.state.organization_id = payload.org
    request.state.user_id = str(user.id)

    return RequestContext(
        user=user,
        organization_id=payload.org,
        role=membership.role if isinstance(membership.role, OrgRole) else OrgRole(membership.role),
    )


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
ActiveSubscriptionContext = Annotated[RequestContext, Depends(enforce_active_subscription)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
