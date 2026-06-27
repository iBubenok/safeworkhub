"""Схемы для работы с материалами базы знаний."""

from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.material import (
    MaterialContentFormat,
    MaterialStatus,
    MaterialType,
    MaterialVisibility,
    NpaActKind,
    NpaLevel,
    NpaStatus,
)


def _validate_http_url(value: str | None) -> str | None:
    """Разрешать только http/https URL — защита от XSS через схему javascript:.

    Поле попадает в href/src на фронте, поэтому опасные схемы (`javascript:`,
    `data:`, `vbscript:` и т. п.) должны отсекаться на бэкенде.
    """
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise ValueError("URL должен начинаться с http:// или https://")
    return value


class MaterialBase(BaseModel):
    """Базовая схема материала."""

    title: str = Field(min_length=1, max_length=500, description="Заголовок")
    summary: str | None = Field(None, max_length=1000, description="Краткое описание")
    type: MaterialType = Field(description="Тип материала")
    category_id: int | None = Field(None, description="ID категории")
    status: MaterialStatus = Field(default=MaterialStatus.DRAFT, description="Статус материала")
    visibility: MaterialVisibility = Field(
        default=MaterialVisibility.ORG,
        description="Видимость материала",
    )


class MaterialCreate(MaterialBase):
    """Схема создания материала."""

    content: str = Field(min_length=1, description="Содержимое (HTML)")


class ArticleCreate(BaseModel):
    """Схема создания статьи (per-type контракт).

    Тип фиксирован (ARTICLE) на стороне сервиса — здесь его нет.
    """

    title: str = Field(min_length=1, max_length=500, description="Заголовок")
    summary: str | None = Field(None, max_length=1000, description="Краткое описание")
    content: str = Field(min_length=1, description="Тело статьи в Markdown")
    content_format: MaterialContentFormat = Field(
        default=MaterialContentFormat.MARKDOWN,
        description="Формат тела",
    )
    category_id: int | None = Field(None, description="ID категории")
    status: MaterialStatus = Field(default=MaterialStatus.DRAFT, description="Статус")
    visibility: MaterialVisibility = Field(default=MaterialVisibility.ORG, description="Видимость")


class TemplateCreate(BaseModel):
    """Схема создания шаблона (per-type контракт).

    Тип фиксирован (TEMPLATE) на стороне сервиса. Файлы загружаются отдельными
    запросами (multipart) после создания материала.
    """

    title: str = Field(min_length=1, max_length=500, description="Заголовок")
    summary: str | None = Field(None, max_length=1000, description="Краткое описание")
    content: str = Field(default="", description="Инструкция по заполнению (необязательно)")
    content_format: MaterialContentFormat = Field(
        default=MaterialContentFormat.MARKDOWN,
        description="Формат тела",
    )
    category_id: int | None = Field(None, description="ID категории")
    status: MaterialStatus = Field(default=MaterialStatus.DRAFT, description="Статус")
    visibility: MaterialVisibility = Field(default=MaterialVisibility.ORG, description="Видимость")


class AttachmentResponse(BaseModel):
    """Метаданные прикреплённого файла (в ответе)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class NewsDetail(BaseModel):
    """Поля, специфичные для новости (в ответе)."""

    model_config = ConfigDict(from_attributes=True)

    source_url: str | None = None
    event_date: date | None = None
    cover_image_url: str | None = None
    tags: list[str] = Field(default_factory=list)


class NewsCreate(BaseModel):
    """Схема создания новости (per-type контракт)."""

    title: str = Field(min_length=1, max_length=500, description="Заголовок")
    summary: str | None = Field(None, max_length=1000, description="Краткое описание")
    content: str = Field(min_length=1, description="Тело новости")
    content_format: MaterialContentFormat = Field(
        default=MaterialContentFormat.MARKDOWN,
        description="Формат тела",
    )
    category_id: int | None = Field(None, description="ID категории")
    status: MaterialStatus = Field(default=MaterialStatus.DRAFT, description="Статус")
    visibility: MaterialVisibility = Field(default=MaterialVisibility.ORG, description="Видимость")
    # Поля, специфичные для новости (все опциональны).
    source_url: str | None = Field(None, max_length=2000, description="Ссылка на первоисточник")
    event_date: date | None = Field(None, description="Дата события/новости")
    cover_image_url: str | None = Field(None, max_length=2000, description="Обложка-превью (URL)")
    tags: list[str] = Field(default_factory=list, description="Теги")

    @field_validator("source_url", "cover_image_url")
    @classmethod
    def _check_url_scheme(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


class MaterialRef(BaseModel):
    """Краткая ссылка на материал (id + заголовок)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str


class NpaDetail(BaseModel):
    """Поля, специфичные для НПА (в ответе)."""

    model_config = ConfigDict(from_attributes=True)

    act_kind: NpaActKind
    level: NpaLevel | None = None
    act_status: NpaStatus | None = None
    document_number: str | None = None
    adoption_date: date | None = None
    effective_date: date | None = None
    revision_date: date | None = None
    issuing_authority: str | None = None
    region: str | None = None
    official_source_url: str | None = None
    replaced_by_id: UUID | None = None
    # Акт-замена (вперёд) и акты, которым этот пришёл на смену (назад) —
    # заполняются вручную в сервисе с учётом видимости.
    replaced_by: MaterialRef | None = None
    replaces: list[MaterialRef] = Field(default_factory=list)


class NpaCreate(BaseModel):
    """Схема создания НПА (per-type контракт)."""

    title: str = Field(min_length=1, max_length=500, description="Название акта")
    summary: str | None = Field(None, max_length=1000, description="Краткая суть")
    content: str = Field(default="", description="Комментарий/применение в ОТ (необязательно)")
    content_format: MaterialContentFormat = Field(default=MaterialContentFormat.MARKDOWN, description="Формат тела")
    category_id: int | None = Field(None, description="ID категории")
    status: MaterialStatus = Field(default=MaterialStatus.DRAFT, description="Статус")
    visibility: MaterialVisibility = Field(default=MaterialVisibility.ORG, description="Видимость")
    # Поля, специфичные для НПА.
    act_kind: NpaActKind = Field(description="Вид акта")
    level: NpaLevel | None = Field(None, description="Уровень (юрисдикция)")
    act_status: NpaStatus | None = Field(None, description="Статус действия")
    document_number: str | None = Field(None, max_length=100, description="Номер документа")
    adoption_date: date | None = Field(None, description="Дата принятия/подписания")
    effective_date: date | None = Field(None, description="Дата вступления в силу")
    revision_date: date | None = Field(None, description="Дата последней редакции")
    issuing_authority: str | None = Field(None, max_length=500, description="Орган, принявший акт")
    region: str | None = Field(None, max_length=255, description="Регион/юрисдикция")
    official_source_url: str | None = Field(None, max_length=2000, description="Ссылка на офиц. публикацию")

    @field_validator("official_source_url")
    @classmethod
    def _check_url_scheme(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


class NpaUpdate(BaseModel):
    """Схема правки реквизитов НПА (все поля опциональны)."""

    act_kind: NpaActKind | None = None
    level: NpaLevel | None = None
    act_status: NpaStatus | None = None
    document_number: str | None = Field(None, max_length=100)
    adoption_date: date | None = None
    effective_date: date | None = None
    revision_date: date | None = None
    issuing_authority: str | None = Field(None, max_length=500)
    region: str | None = Field(None, max_length=255)
    official_source_url: str | None = Field(None, max_length=2000)
    replaced_by_id: UUID | None = None

    @field_validator("official_source_url")
    @classmethod
    def _check_url_scheme(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


class MaterialUpdate(BaseModel):
    """Схема обновления материала."""

    title: str | None = Field(None, min_length=1, max_length=500)
    summary: str | None = None
    content: str | None = None
    content_format: MaterialContentFormat | None = None
    type: MaterialType | None = None
    category_id: int | None = None
    status: MaterialStatus | None = None
    visibility: MaterialVisibility | None = None
    # Примечание к версии (не поле материала). Сохраняется в истории при правке контента.
    change_note: str | None = Field(None, max_length=500, description="Примечание к изменению")


class MaterialVersionResponse(BaseModel):
    """Версия материала (для истории)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_no: int
    editor_id: UUID | None = None
    editor_name: str | None = None
    change_note: str | None = None
    created_at: datetime
    snapshot: dict[str, Any]


class MaterialResponse(MaterialBase):
    """Схема ответа с материалом."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: int
    author_id: UUID
    author_name: str | None = None
    organization_name: str | None = None
    content: str
    content_format: MaterialContentFormat
    views_count: int
    status: MaterialStatus
    published_at: datetime | None
    updated_by_id: UUID | None = None
    updated_by_name: str | None = None
    created_at: datetime
    updated_at: datetime
    # Деталь для типа «Новость» (для остальных типов — None). Заполняется вручную
    # в сервисе; validation_alias не даёт model_validate(material) читать ленивую
    # связь material.news (иначе MissingGreenlet в async-контексте).
    news: NewsDetail | None = Field(default=None, validation_alias="news_detail")
    # Деталь НПА (для остальных типов — None). Alias не совпадает с именем связи Material.npa,
    # чтобы model_validate(material) не читал ленивую связь; заполняется вручную в сервисе.
    npa: NpaDetail | None = Field(default=None, validation_alias="npa_detail")
    # Прикреплённые файлы. Alias не совпадает с именем связи Material.attachments,
    # чтобы model_validate(material) не читал ленивую коллекцию (MissingGreenlet);
    # заполняется вручную в сервисе.
    attachments: list[AttachmentResponse] = Field(default_factory=list, validation_alias="attachments_src")


class MaterialListItem(BaseModel):
    """Краткая информация о материале для списков."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: int
    organization_name: str | None = None
    title: str
    summary: str | None
    type: MaterialType
    status: MaterialStatus
    views_count: int
    published_at: datetime | None
    visibility: MaterialVisibility
    attachment_count: int = 0


class MaterialListResponse(BaseModel):
    """Ответ со списком материалов."""

    items: list[MaterialListItem]
    total: int
    page: int
    page_size: int
    pages: int


class SearchRequest(BaseModel):
    """Запрос на поиск материалов."""

    query: str = Field(min_length=2, max_length=200, description="Поисковый запрос")
    type: MaterialType | None = Field(None, description="Фильтр по типу")
    category_id: int | None = Field(None, description="Фильтр по категории")
    status: MaterialStatus | None = Field(None, description="Статус: published (по умолч.), draft, archived")
    page: int = Field(default=1, ge=1, description="Номер страницы")
    page_size: int = Field(default=20, ge=1, le=100, description="Размер страницы")


class SearchResult(MaterialListItem):
    """Результат поиска с дополнительными полями."""

    highlights: dict[str, str] | None = Field(
        None,
        description="Подсвеченные фрагменты (title, content)",
    )


class SearchResponse(BaseModel):
    """Ответ на поисковый запрос."""

    items: list[SearchResult]
    total: int
    query: str
    page: int
    page_size: int
    pages: int


class CategoryResponse(BaseModel):
    """Схема категории."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    slug: str
    parent_id: int | None
    description: str | None
    sort_order: int


class CategoryCreate(BaseModel):
    """Создание/обновление категории."""

    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(
        default=None,
        description="Slug категории, если не указан — генерируется автоматически",
    )
    parent_id: int | None = None
    description: str | None = None
    sort_order: int = Field(default=0, ge=0)
