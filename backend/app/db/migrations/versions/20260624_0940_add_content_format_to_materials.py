"""add content_format to materials

Revision ID: c4d5e6f70811
Revises: 8ed3dc0a3dd2
Create Date: 2026-06-24 09:40:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "c4d5e6f70811"
down_revision: str | None = "8ed3dc0a3dd2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Enum создаётся явно ниже, поэтому create_type=False (как в начальной миграции).
content_format_enum = postgresql.ENUM(
    "markdown",
    "html",
    name="material_content_format",
    create_type=False,
)


def upgrade() -> None:
    """Добавляет формат тела материала (markdown/html)."""
    content_format_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "materials",
        sa.Column(
            "content_format",
            content_format_enum,
            nullable=False,
            server_default="markdown",
        ),
    )
    # Серверный дефолт нужен только чтобы бекфилить существующие строки;
    # дальше значение задаётся на уровне ORM, поэтому снимаем его.
    op.alter_column("materials", "content_format", server_default=None)


def downgrade() -> None:
    """Удаляет формат тела материала."""
    op.drop_column("materials", "content_format")
    op.execute("DROP TYPE IF EXISTS material_content_format")
