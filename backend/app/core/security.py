"""Модуль безопасности: хэширование паролей, JWT-токены и вспомогательные функции."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings

# Контекст для хэширования паролей (Argon2)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TokenType(StrEnum):
    """Типы поддерживаемых JWT токенов."""

    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    """Базовая нагрузка JWT токена."""

    sub: UUID
    type: TokenType
    exp: datetime
    iat: datetime
    org: int | None = None
    roles: list[str] = Field(default_factory=list)
    sid: UUID | None = None
    fam: UUID | None = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля по хэшу."""
    return bool(pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    """Хэширование пароля."""
    return str(pwd_context.hash(password))


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(
    user_id: UUID,
    *,
    organization_id: int | None,
    roles: list[str],
    expires_minutes: int | None = None,
) -> str:
    """Создание access-токена."""
    issued_at = _now()
    expires_delta = timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    expire = issued_at + expires_delta

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": TokenType.ACCESS.value,
        "iat": issued_at,
        "exp": expire,
        "org": organization_id,
        "roles": roles,
        "jti": str(uuid4()),
    }

    token: str = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token


def create_refresh_token(
    user_id: UUID,
    *,
    session_id: UUID,
    family_id: UUID,
    expires_days: int | None = None,
) -> str:
    """Создание refresh-токена с ротацией."""
    issued_at = _now()
    expire = issued_at + timedelta(days=expires_days or settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "type": TokenType.REFRESH.value,
        "iat": issued_at,
        "exp": expire,
        "sid": str(session_id),
        "fam": str(family_id),
    }
    token: str = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_token(raw_token: str) -> TokenPayload | None:
    """Декодирование и валидация JWT токена."""
    try:
        payload = jwt.decode(
            raw_token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload.model_validate(payload)
    except (JWTError, ValidationError):
        return None


def verify_token(raw_token: str, expected_type: TokenType) -> TokenPayload | None:
    """Верификация токена и проверка типа."""
    payload = decode_token(raw_token)
    if payload is None:
        return None
    if payload.type != expected_type:
        return None
    return payload


def generate_session_family() -> tuple[UUID, UUID]:
    """Создать идентификаторы для refresh-сессии и её семейства."""
    return uuid4(), uuid4()


def hash_token(token: str) -> str:
    """Возвращает криптографический хэш токена для хранения в БД."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_reset_token() -> str:
    """Генерация одноразового токена для операций восстановления."""
    return secrets.token_urlsafe(48)
