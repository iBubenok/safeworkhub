"""Схемы для работы с пользователями."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    email: EmailStr = Field(description="Email пользователя")
    name: str = Field(min_length=1, max_length=255, description="Имя пользователя")


class UserCreate(UserBase):
    """Схема создания пользователя."""

    password: str = Field(
        min_length=8,
        max_length=100,
        description="Пароль (минимум 8 символов)",
    )


class UserUpdate(BaseModel):
    """Схема обновления пользователя (partial update)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """Схема ответа с данными пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserInDB(UserResponse):
    """Схема пользователя в БД (с хэшем пароля)."""

    password_hash: str
    is_superuser: bool


class UserWithOrganizations(UserResponse):
    """Схема пользователя с организациями."""

    organizations: list["OrganizationMembership"] = []


class OrganizationMembership(BaseModel):
    """Членство в организации."""

    model_config = ConfigDict(from_attributes=True)

    organization_id: int
    organization_name: str
    role: str
    joined_at: datetime
