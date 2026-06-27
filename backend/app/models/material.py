"""Модели базы знаний: материалы и категории."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IntegerPKMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attachment import MaterialAttachment
    from app.models.material_version import MaterialVersion
    from app.models.news import News
    from app.models.npa import Npa
    from app.models.organization import Organization
    from app.models.user import User


class MaterialType(StrEnum):
    """Типы материалов базы знаний."""

    ARTICLE = "article"
    NPA = "npa"
    TEMPLATE = "template"
    REFERENCE = "reference"
    NEWS = "news"


class MaterialStatus(StrEnum):
    """Статусы материала."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class MaterialVisibility(StrEnum):
    """Видимость материалов."""

    ORG = "org"
    PUBLIC = "public"


class MaterialContentFormat(StrEnum):
    """Формат тела материала."""

    MARKDOWN = "markdown"
    HTML = "html"


class NpaActKind(StrEnum):
    """Вид нормативно-правового акта."""

    FEDERAL_LAW = "federal_law"
    CONSTITUTIONAL_LAW = "constitutional_law"
    CODE = "code"
    PRESIDENTIAL_DECREE = "presidential_decree"
    GOVERNMENT_DECREE = "government_decree"
    MINISTRY_ORDER = "ministry_order"
    GOST = "gost"
    SANPIN = "sanpin"
    SP = "sp"
    REGIONAL_LAW = "regional_law"
    MUNICIPAL_ACT = "municipal_act"
    LOCAL_ACT = "local_act"
    OTHER = "other"


class NpaLevel(StrEnum):
    """Уровень (юрисдикция) акта."""

    FEDERAL = "federal"
    REGIONAL = "regional"
    MUNICIPAL = "municipal"
    LOCAL = "local"


class NpaStatus(StrEnum):
    """Статус действия акта."""

    IN_FORCE = "in_force"
    NOT_IN_FORCE = "not_in_force"
    REPEALED = "repealed"
    AMENDED = "amended"
    SUSPENDED = "suspended"


class Category(Base, IntegerPKMixin, TimestampMixin):
    """Категория материалов (иерархия поддерживается через parent_id)."""

    __tablename__ = "categories"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
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
    organization: Mapped["Organization"] = relationship(back_populates="categories")

    __table_args__ = (
        Index("ix_categories_parent_id", "parent_id"),
        Index("ix_categories_org", "organization_id"),
        Index("ix_categories_slug", "slug"),
        # Уникальность slug в пределах организации
        UniqueConstraint("organization_id", "slug", name="uq_category_org_slug"),
    )

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Material(Base, UUIDMixin, TimestampMixin):
    """Материал базы знаний."""

    __tablename__ = "materials"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_format: Mapped[MaterialContentFormat] = mapped_column(
        Enum(
            MaterialContentFormat,
            name="material_content_format",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=MaterialContentFormat.MARKDOWN,
    )
    summary: Mapped[str | None] = mapped_column(String(1000))
    type: Mapped[MaterialType] = mapped_column(
        Enum(
            MaterialType,
            name="material_type",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=MaterialType.ARTICLE,
    )
    status: Mapped[MaterialStatus] = mapped_column(
        Enum(
            MaterialStatus,
            name="material_status",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=MaterialStatus.DRAFT,
    )
    visibility: Mapped[MaterialVisibility] = mapped_column(
        Enum(
            MaterialVisibility,
            name="material_visibility",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=MaterialVisibility.ORG,
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

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
    organization: Mapped["Organization"] = relationship(back_populates="materials")
    author: Mapped["User"] = relationship(
        back_populates="materials",
        foreign_keys=[author_id],
    )
    updated_by: Mapped["User | None"] = relationship(
        foreign_keys=[updated_by_id],
        lazy="selectin",
    )
    # Деталь для типа «Новость» (1:1). Для остальных типов — None.
    news: Mapped["News | None"] = relationship(
        back_populates="material",
        uselist=False,
        cascade="all, delete-orphan",
    )
    # Прикреплённые файлы (1:много). Используются шаблонами.
    attachments: Mapped[list["MaterialAttachment"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
        order_by="MaterialAttachment.created_at",
    )
    # Деталь для типа «НПА» (1:1). Для остальных типов — None.
    # foreign_keys явно: у Npa два FK на materials (material_id и replaced_by_id).
    npa: Mapped["Npa | None"] = relationship(
        back_populates="material",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="Npa.material_id",
    )
    # История версий (1:много). Снимки версионируемых полей.
    versions: Mapped[list["MaterialVersion"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
        order_by="MaterialVersion.version_no",
    )

    __table_args__ = (
        Index("ix_materials_type", "type"),
        Index("ix_materials_category_id", "category_id"),
        Index("ix_materials_published_at", "published_at"),
        Index("ix_materials_org", "organization_id"),
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
        return self.published_at <= datetime.now(UTC)

    def __repr__(self) -> str:
        return f"<Material {self.title[:50]}>"
