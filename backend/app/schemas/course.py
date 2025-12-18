"""Схемы для LMS-курсов и назначений."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.course import AssignmentStatus


class CourseModuleInput(BaseModel):
    """Данные модуля при создании курса."""

    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    sort_order: int = Field(default=0, ge=0)
    duration_minutes: int = Field(default=0, ge=0)


class CourseCreate(BaseModel):
    """Создание курса."""

    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    duration_minutes: int = Field(default=0, ge=0)
    is_published: bool = False
    thumbnail_url: str | None = None
    modules: list[CourseModuleInput] = Field(default_factory=list)


class CourseUpdate(BaseModel):
    """Обновление курса."""

    title: str | None = None
    description: str | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    is_published: bool | None = None
    thumbnail_url: str | None = None
    modules: list[CourseModuleInput] | None = None


class CourseModuleResponse(CourseModuleInput):
    """Ответ с модулем курса."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class CourseResponse(BaseModel):
    """Ответ с курсом."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    title: str
    description: str | None
    duration_minutes: int
    is_published: bool
    thumbnail_url: str | None
    created_at: datetime
    updated_at: datetime
    modules: list[CourseModuleResponse] = []


class CourseAssignmentResponse(BaseModel):
    """Ответ с назначением курса пользователю."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: int
    organization_id: int
    user_id: UUID
    status: AssignmentStatus
    progress_percent: int
    due_at: datetime | None
    completed_at: datetime | None
    last_activity_at: datetime | None
    created_at: datetime
    updated_at: datetime
