"""create news detail table

Revision ID: d5e6f7081119
Revises: c4d5e6f70811
Create Date: 2026-06-24 12:30:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "d5e6f7081119"
down_revision: str | None = "c4d5e6f70811"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт деталь-таблицу новостей (1:1 к materials)."""
    op.create_table(
        "news",
        sa.Column("material_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_url", sa.String(length=2000), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=2000), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("material_id"),
    )
    # GIN-индекс под будущую фильтрацию по тегам (tags @> ARRAY[...]).
    op.create_index("ix_news_tags", "news", ["tags"], postgresql_using="gin")


def downgrade() -> None:
    """Удаляет деталь-таблицу новостей."""
    op.drop_index("ix_news_tags", table_name="news")
    op.drop_table("news")
