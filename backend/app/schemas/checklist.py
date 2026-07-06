"""Схемы подмодуля «Чек-листы» (древовидные пункты)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.checklist import ChecklistAnswerType, ChecklistNodeType, ChecklistStatus, ChecklistVisibility


class ChecklistReferenceInput(BaseModel):
    """Ссылка пункта при создании/правке (материал и/или заметка)."""

    material_id: UUID | None = Field(None, description="Ссылка на материал (НПА/статью)")
    note: str | None = Field(None, max_length=500, description="Заметка (напр. пункт закона)")


class ChecklistNodeInput(BaseModel):
    """Узел чек-листа при создании/правке (рекурсивно: группа с детьми или пункт-лист)."""

    node_type: ChecklistNodeType = ChecklistNodeType.ITEM
    text: str = Field(min_length=1, description="Заголовок раздела или текст пункта")
    answer_type: ChecklistAnswerType | None = Field(None, description="Тип ответа (только у пункта)")
    required: bool = Field(default=True, description="Обязательный пункт")
    help_text: str | None = Field(None, description="Подсказка")
    references: list[ChecklistReferenceInput] = Field(default_factory=list, description="Ссылки пункта")
    children: list["ChecklistNodeInput"] = Field(default_factory=list, description="Вложенные узлы")

    @model_validator(mode="after")
    def _validate_node(self) -> "ChecklistNodeInput":
        if self.node_type == ChecklistNodeType.ITEM:
            if self.answer_type is None:
                raise ValueError("У пункта должен быть указан тип ответа")
            if self.children:
                raise ValueError("Пункт не может содержать вложенные узлы")
        return self


class ChecklistReferenceResponse(BaseModel):
    """Ссылка пункта в ответе."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    material_id: UUID | None = None
    material_title: str | None = None
    note: str | None = None


class ChecklistNodeResponse(BaseModel):
    """Узел чек-листа в ответе (рекурсивно)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    node_type: ChecklistNodeType
    text: str
    answer_type: ChecklistAnswerType | None = None
    required: bool
    help_text: str | None = None
    references: list[ChecklistReferenceResponse] = Field(default_factory=list)
    children: list["ChecklistNodeResponse"] = Field(default_factory=list)


ChecklistNodeInput.model_rebuild()
ChecklistNodeResponse.model_rebuild()


class ChecklistCreate(BaseModel):
    """Создание чек-листа через конструктор."""

    title: str = Field(min_length=1, max_length=500, description="Название")
    description: str | None = Field(None, description="Описание")
    status: ChecklistStatus = Field(default=ChecklistStatus.DRAFT, description="Статус")
    visibility: ChecklistVisibility = Field(default=ChecklistVisibility.ORG, description="Видимость")
    items: list[ChecklistNodeInput] = Field(default_factory=list, description="Дерево пунктов/разделов")


class ChecklistUpdate(BaseModel):
    """Правка чек-листа. Если items переданы — заменяют всё дерево."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: ChecklistStatus | None = None
    visibility: ChecklistVisibility | None = None
    items: list[ChecklistNodeInput] | None = None


class ChecklistResponse(BaseModel):
    """Полный чек-лист с деревом пунктов."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: int
    organization_name: str | None = None
    author_id: UUID
    author_name: str | None = None
    title: str
    description: str | None
    status: ChecklistStatus
    visibility: ChecklistVisibility = ChecklistVisibility.ORG
    views_count: int = 0
    created_at: datetime
    updated_at: datetime
    updated_by_name: str | None = None
    items: list[ChecklistNodeResponse] = Field(default_factory=list)


class ChecklistListItem(BaseModel):
    """Краткая карточка чек-листа для списка."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: ChecklistStatus
    visibility: ChecklistVisibility = ChecklistVisibility.ORG
    organization_name: str | None = None
    item_count: int = 0
    views_count: int = 0
    runs_count: int = 0
    created_at: datetime


class ChecklistListResponse(BaseModel):
    """Ответ со списком чек-листов."""

    items: list[ChecklistListItem]
    total: int
    page: int
    page_size: int
    pages: int
