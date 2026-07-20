"""Схемы для LMS-курсов и назначений."""

from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.course import AssignmentStatus


def _validate_http_url(value: str | None) -> str | None:
    """Разрешать только http/https URL — защита от XSS через схему javascript:."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise ValueError("URL должен начинаться с http:// или https://")
    return value


class CourseCreate(BaseModel):
    """Создание курса."""

    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    content: str | None = None
    duration_minutes: int = Field(default=0, ge=0)
    is_published: bool = False
    thumbnail_url: str | None = None
    training_basis: str | None = Field(default=None, max_length=500, description="Основание обучения")
    training_basis_url: str | None = Field(default=None, max_length=2000, description="Ссылка на основание")

    @field_validator("training_basis_url")
    @classmethod
    def _check_url(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


class CourseUpdate(BaseModel):
    """Обновление курса."""

    title: str | None = None
    description: str | None = None
    content: str | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    is_published: bool | None = None
    thumbnail_url: str | None = None
    training_basis: str | None = Field(default=None, max_length=500)
    training_basis_url: str | None = Field(default=None, max_length=2000)

    @field_validator("training_basis_url")
    @classmethod
    def _check_url(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


class CourseResponse(BaseModel):
    """Ответ с курсом."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    title: str
    description: str | None
    content: str | None
    duration_minutes: int
    is_published: bool
    thumbnail_url: str | None
    training_basis: str | None
    training_basis_url: str | None
    created_at: datetime
    updated_at: datetime


class CourseAssignmentResponse(BaseModel):
    """Ответ с назначением курса пользователю."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: int
    course_title: str | None = None
    organization_id: int
    user_id: UUID
    status: AssignmentStatus
    progress_percent: int
    due_at: datetime | None
    completed_at: datetime | None
    last_activity_at: datetime | None
    created_at: datetime
    updated_at: datetime
