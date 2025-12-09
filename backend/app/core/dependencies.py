"""FastAPI зависимости для внедрения в эндпоинты."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import verify_token
from app.db.session import get_session
from app.db.repositories.user_repository import UserRepository
from app.models import User

# Схема аутентификации Bearer
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User | None:
    """Получение текущего пользователя (опционально).

    Возвращает None если токен не предоставлен.
    Выбрасывает исключение если токен невалиден.
    """
    if credentials is None:
        return None

    user_id = verify_token(credentials.credentials, token_type="access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен доступа",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repository = UserRepository(session)
    user = await repository.get_by_id(UUID(user_id))

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или деактивирован",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    """Получение текущего пользователя (обязательно).

    Выбрасывает исключение если пользователь не аутентифицирован.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_superuser(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Получение текущего суперпользователя.

    Выбрасывает исключение если пользователь не суперпользователь.
    """
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return user


# Типизированные зависимости для удобства использования
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
CurrentSuperuser = Annotated[User, Depends(get_current_active_superuser)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
