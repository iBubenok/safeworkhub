"""Схемы подмодуля «Проверки» (проведение проверки по чек-листу)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.checklist import ChecklistAnswerType
from app.models.checklist_run import ChecklistRunResult, ChecklistRunStatus


class AssigneeInfo(BaseModel):
    """Краткая информация о назначенном на проверку сотруднике."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class ChecklistRunCreate(BaseModel):
    """Старт проверки по опубликованному чек-листу."""

    checklist_id: UUID = Field(description="Чек-лист, по которому проводится проверка")
    title: str | None = Field(None, max_length=500, description="Название проверки/объекта (по умолчанию — чек-лист)")
    assignee_ids: list[UUID] = Field(
        default_factory=list,
        description="Сотрудники организации, назначенные на проведение проверки (помимо создателя)",
    )


class ChecklistRunAssigneesUpdate(BaseModel):
    """Изменение состава назначенных на проверку."""

    assignee_ids: list[UUID] = Field(description="Полный новый список назначенных сотрудников")


class ChecklistRunAnswerInput(BaseModel):
    """Ответ на один пункт проверки."""

    answer_id: UUID = Field(description="ID строки-ответа проверки")
    value: str | None = Field(None, description="Значение ответа в каноническом виде")
    comment: str | None = Field(None, description="Комментарий проверяющего")


class ChecklistRunUpdate(BaseModel):
    """Сохранение хода проверки (частично)."""

    title: str | None = Field(None, max_length=500)
    notes: str | None = Field(None, description="Общий комментарий по проверке")
    answers: list[ChecklistRunAnswerInput] | None = Field(None, description="Ответы для обновления")


class ChecklistRunAnswerResponse(BaseModel):
    """Строка-ответ проверки в ответе API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sort_order: int
    group_title: str | None = None
    item_text: str
    help_text: str | None = None
    answer_type: ChecklistAnswerType
    required: bool
    references: list[dict[str, Any]] = Field(default_factory=list)
    value: str | None = None
    comment: str | None = None


class ChecklistRunResponse(BaseModel):
    """Полная проверка с ответами."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: int
    checklist_id: UUID | None = None
    checklist_title: str
    title: str | None = None
    conducted_by_id: UUID
    conducted_by_name: str | None = None
    assignees: list[AssigneeInfo] = Field(default_factory=list)
    status: ChecklistRunStatus
    result: ChecklistRunResult | None = None
    gradable_count: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    not_applicable_count: int = 0
    score: float | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    answers: list[ChecklistRunAnswerResponse] = Field(default_factory=list)


class ChecklistRunListItem(BaseModel):
    """Краткая карточка проверки для списка."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    checklist_title: str
    status: ChecklistRunStatus
    result: ChecklistRunResult | None = None
    gradable_count: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    score: float | None = None
    conducted_by_name: str | None = None
    assignees: list[AssigneeInfo] = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime | None = None


class ChecklistRunListResponse(BaseModel):
    """Ответ со списком проверок."""

    items: list[ChecklistRunListItem]
    total: int
    page: int
    page_size: int
    pages: int
