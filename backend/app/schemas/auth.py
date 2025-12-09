"""Схемы для аутентификации."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Запрос на вход в систему."""

    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(description="Пароль")


class TokenResponse(BaseModel):
    """Ответ с токенами доступа."""

    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Тип токена")
    expires_in: int = Field(description="Время жизни access token в секундах")


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена."""

    refresh_token: str = Field(description="Refresh token")


class RegisterRequest(BaseModel):
    """Запрос на регистрацию организации."""

    # Данные организации
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

    # Данные администратора
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
    user_id: str = Field(description="ID созданного пользователя")
    message: str = Field(
        default="Регистрация успешна. Проверьте email для подтверждения.",
        description="Сообщение",
    )


class PasswordResetRequest(BaseModel):
    """Запрос на сброс пароля."""

    email: EmailStr = Field(description="Email пользователя")


class PasswordResetConfirm(BaseModel):
    """Подтверждение сброса пароля."""

    token: str = Field(description="Токен сброса пароля")
    new_password: str = Field(
        min_length=8,
        max_length=100,
        description="Новый пароль",
    )
