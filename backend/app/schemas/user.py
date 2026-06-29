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
    role: str = Field(default="member", description="Роль в организации")


class UserUpdate(BaseModel):
    """Схема обновления пользователя (partial update)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    is_active: bool | None = None
    role: str | None = Field(default=None, description="Роль в организации")


class UserResponse(UserBase):
    """Схема ответа с данными пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_superuser: bool = False
    primary_organization_id: int | None = None
    role: str | None = None
    created_at: datetime
    updated_at: datetime


class MembershipResponse(BaseModel):
    """Членство пользователя в организации."""

    model_config = ConfigDict(from_attributes=True)

    organization_id: int
    role: str
    is_active: bool
    joined_at: datetime


class UserWithMemberships(UserResponse):
    """Пользователь с привязками к организациям."""

    memberships: list[MembershipResponse] = []
