"""create material versions table

Revision ID: a1b2c3d4e5f6
Revises: f7081119aa01
Create Date: 2026-06-25 17:30:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f7081119aa01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт таблицу версий материалов и заполняет v1 для существующих."""
    op.create_table(
        "material_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("editor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_note", sa.String(length=500), nullable=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["editor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("material_id", "version_no", name="uq_material_version_no"),
    )
    op.create_index("ix_material_versions_material_id", "material_versions", ["material_id"])

    # Бэкфилл: v1 для всех существующих материалов из текущего состояния.
    op.execute(
        """
        INSERT INTO material_versions (id, material_id, version_no, editor_id, change_note, snapshot, created_at)
        SELECT gen_random_uuid(), m.id, 1, m.author_id, NULL,
               json_build_object(
                   'title', m.title,
                   'summary', m.summary,
                   'content', m.content,
                   'content_format', m.content_format::text
               ),
               m.created_at
        FROM materials m
        """
    )


def downgrade() -> None:
    """Удаляет таблицу версий материалов."""
    op.drop_index("ix_material_versions_material_id", table_name="material_versions")
    op.drop_table("material_versions")
