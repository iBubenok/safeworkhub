"""Модели базы знаний: материалы, категории, документы."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IntegerPKMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    pass


class MaterialType(StrEnum):
    """Типы материалов базы знаний."""

    ARTICLE = "article"       # Экспертная статья
    NPA = "npa"               # Нормативно-правовой акт
    TEMPLATE = "template"     # Шаблон документа
    REFERENCE = "reference"   # Справочный материал
    NEWS = "news"             # Новость


class Category(Base, IntegerPKMixin, TimestampMixin):
    """Категория материалов.

    Иерархическая структура для организации материалов базы знаний.

    Attributes:
        id: Целочисленный ID.
        name: Название категории.
        slug: URL-slug для категории.
        parent_id: ID родительской категории (для иерархии).
        sort_order: Порядок сортировки.
        description: Описание категории.
    """

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Связи
    parent: Mapped["Category | None"] = relationship(
        back_populates="children",
        remote_side="Category.id",
    )
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    materials: Mapped[list["Material"]] = relationship(back_populates="category")

    __table_args__ = (
        Index("ix_categories_slug", "slug"),
        Index("ix_categories_parent_id", "parent_id"),
    )

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Material(Base, UUIDMixin, TimestampMixin):
    """Материал базы знаний.

    Основная сущность контента: статьи, НПА, шаблоны и т.д.
    Поддерживает полнотекстовый поиск через PostgreSQL FTS.

    Attributes:
        id: UUID материала.
        title: Заголовок.
        content: Содержимое (HTML).
        type: Тип материала.
        category_id: ID категории.
        published_at: Дата публикации.
        views_count: Количество просмотров.
        search_vector: Вектор для полнотекстового поиска.
    """

    __tablename__ = "materials"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(1000))
    type: Mapped[MaterialType] = mapped_column(
        Enum(MaterialType, name="material_type"),
        nullable=False,
        default=MaterialType.ARTICLE,
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Вычисляемый столбец для полнотекстового поиска
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('russian', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('russian', coalesce(summary, '')), 'B') || "
            "setweight(to_tsvector('russian', coalesce(content, '')), 'C')",
            persisted=True,
        ),
    )

    # Связи
    category: Mapped["Category | None"] = relationship(back_populates="materials")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_materials_type", "type"),
        Index("ix_materials_category_id", "category_id"),
        Index("ix_materials_published_at", "published_at"),
        Index(
            "ix_materials_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    @property
    def is_published(self) -> bool:
        """Проверка, опубликован ли материал."""
        if self.published_at is None:
            return False
        return self.published_at <= datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Material {self.title[:50]}>"


class Document(Base, UUIDMixin, TimestampMixin):
    """Прикреплённый документ (файл).

    Файлы, связанные с материалами: шаблоны в DOCX, PDF и т.д.

    Attributes:
        id: UUID документа.
        title: Название документа.
        material_id: ID связанного материала.
        file_path: Путь к файлу в хранилище.
        file_name: Оригинальное имя файла.
        file_size: Размер файла в байтах.
        mime_type: MIME-тип файла.
        downloads_count: Количество скачиваний.
    """

    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    material_id: Mapped[str] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    downloads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Связи
    material: Mapped["Material"] = relationship(back_populates="documents")

    __table_args__ = (
        Index("ix_documents_material_id", "material_id"),
    )

    def __repr__(self) -> str:
        return f"<Document {self.file_name}>"
