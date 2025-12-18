"""Схемы для аутентификации и управления сессиями."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Запрос на вход в систему."""

    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(description="Пароль")
    organization_id: int | None = Field(
        default=None,
        description="Организация, в которую выполняется вход (если несколько)",
    )


class TokenResponse(BaseModel):
    """Ответ с токенами доступа."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Тип токена")
    expires_in: int = Field(description="Время жизни access token в секундах")
    refresh_expires_in: int = Field(description="Время жизни refresh token в секундах")
    organization_id: int = Field(description="Текущая организация пользователя")
    role: str = Field(description="Роль пользователя в организации")
    user: UserResponse
    refresh_token: str | None = Field(
        default=None,
        exclude=True,
        description="Refresh token (используется только для установки cookie)",
    )


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена.

    По умолчанию backend ожидает refresh-токен в httpOnly cookie,
    но поле оставлено для совместимости с тестовыми сценариями.
    """

    refresh_token: str | None = Field(
        default=None,
        description="Refresh token (если не используется cookie)",
    )


class RegisterRequest(BaseModel):
    """Запрос на регистрацию организации и владельца."""

    organization_name: str = Field(
        min_length=1,
        max_length=500,
        description="Название организации",
    )
    inn: str = Field(
        min_length=10,
        max_length=12,
        pattern=r"^\d{10,12}$",
        description="ИНН организации (10 или 12 цифр)",
    )
    admin_email: EmailStr = Field(description="Email администратора")
    admin_password: str = Field(
        min_length=8,
        max_length=100,
        description="Пароль администратора",
    )
    admin_name: str = Field(
        min_length=1,
        max_length=255,
        description="Имя администратора",
    )


class RegisterResponse(BaseModel):
    """Ответ на регистрацию."""

    organization_id: int = Field(description="ID созданной организации")
    user_id: UUID = Field(description="ID созданного пользователя")
    subscription_status: str = Field(description="Статус подписки")
    trial_ends_at: datetime | None = Field(description="Окончание пробного периода")


class ActiveSession(BaseModel):
    """Данные активной сессии для фронтенда."""

    model_config = ConfigDict(from_attributes=True)

    user: UserResponse
    organization_id: int
    role: str
