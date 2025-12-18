"""Схемы для работы с организациями."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """Базовая схема организации."""

    name: str = Field(min_length=1, max_length=500, description="Название организации")
    inn: str = Field(
        min_length=10,
        max_length=12,
        pattern=r"^\d{10,12}$",
        description="ИНН организации",
    )
    description: str | None = Field(None, description="Описание организации")


class OrganizationCreate(OrganizationBase):
    """Схема создания организации."""

    pass


class OrganizationUpdate(BaseModel):
    """Схема обновления организации (partial update)."""

    name: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    logo_url: str | None = None


class OrganizationResponse(OrganizationBase):
    """Схема ответа с данными организации."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    logo_url: str | None
    owner_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class OrganizationWithSubscription(OrganizationResponse):
    """Организация с информацией о подписке."""

    subscription: "SubscriptionInfo | None" = None
    users_count: int = 0


class SubscriptionInfo(BaseModel):
    """Краткая информация о подписке."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    tariff_name: str
    valid_until: datetime | None
    trial_ends_at: datetime | None
    max_users: int
