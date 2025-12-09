"""Модуль безопасности: хэширование паролей, JWT-токены."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Контекст для хэширования паролей (Argon2)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля по хэшу.

    Args:
        plain_password: Открытый пароль.
        hashed_password: Хэш пароля.

    Returns:
        True если пароль верный.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хэширование пароля.

    Args:
        password: Открытый пароль.

    Returns:
        Хэш пароля.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Создание JWT access token.

    Args:
        subject: Идентификатор субъекта (обычно user_id).
        expires_delta: Время жизни токена.
        additional_claims: Дополнительные claims.

    Returns:
        Закодированный JWT токен.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Создание JWT refresh token.

    Args:
        subject: Идентификатор субъекта.
        expires_delta: Время жизни токена.

    Returns:
        Закодированный JWT токен.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Декодирование JWT токена.

    Args:
        token: JWT токен.

    Returns:
        Payload токена или None при ошибке.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> str | None:
    """Верификация токена и извлечение subject.

    Args:
        token: JWT токен.
        token_type: Ожидаемый тип токена ("access" или "refresh").

    Returns:
        Subject (user_id) или None при ошибке.
    """
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    return payload.get("sub")
