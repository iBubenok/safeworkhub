"""Схемы для работы с материалами базы знаний."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.material import MaterialContentFormat, MaterialStatus, MaterialType, MaterialVisibility


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


class MaterialListItem(BaseModel):
    """Краткая информация о материале для списков."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: int
    title: str
    summary: str | None
    type: MaterialType
    status: MaterialStatus
    views_count: int
    published_at: datetime | None
    visibility: MaterialVisibility


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
