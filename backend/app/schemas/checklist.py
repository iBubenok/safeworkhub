"""Схемы подмодуля «Чек-листы»."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.checklist import ChecklistAnswerType, ChecklistStatus


class ChecklistItemInput(BaseModel):
    """Пункт чек-листа при создании/правке."""

    text: str = Field(min_length=1, description="Текст вопроса")
    answer_type: ChecklistAnswerType = Field(description="Тип ответа")
    required: bool = Field(default=True, description="Обязательный пункт")
    help_text: str | None = Field(None, description="Подсказка")
    reference_material_id: UUID | None = Field(None, description="Ссылка на материал (НПА/статью)")
    reference_note: str | None = Field(None, max_length=500, description="Заметка к ссылке (пункт закона)")


class ChecklistItemResponse(BaseModel):
    """Пункт чек-листа в ответе."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sort_order: int
    text: str
    answer_type: ChecklistAnswerType
    required: bool
    help_text: str | None = None
    reference_material_id: UUID | None = None
    reference_material_title: str | None = None
    reference_note: str | None = None


class ChecklistCreate(BaseModel):
    """Создание чек-листа через конструктор."""

    title: str = Field(min_length=1, max_length=500, description="Название")
    description: str | None = Field(None, description="Описание")
    status: ChecklistStatus = Field(default=ChecklistStatus.DRAFT, description="Статус")
    items: list[ChecklistItemInput] = Field(default_factory=list, description="Пункты чек-листа")


class ChecklistUpdate(BaseModel):
    """Правка чек-листа. Если items переданы — заменяют все пункты."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: ChecklistStatus | None = None
    items: list[ChecklistItemInput] | None = None


class ChecklistResponse(BaseModel):
    """Полный чек-лист с пунктами."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: int
    author_id: UUID
    author_name: str | None = None
    title: str
    description: str | None
    status: ChecklistStatus
    created_at: datetime
    updated_at: datetime
    updated_by_name: str | None = None
    items: list[ChecklistItemResponse] = Field(default_factory=list)


class ChecklistListItem(BaseModel):
    """Краткая карточка чек-листа для списка."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: ChecklistStatus
    item_count: int = 0
    created_at: datetime


class ChecklistListResponse(BaseModel):
    """Ответ со списком чек-листов."""

    items: list[ChecklistListItem]
    total: int
    page: int
    page_size: int
    pages: int
