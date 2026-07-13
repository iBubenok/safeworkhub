"""course content field, drop course_modules

Revision ID: c7a2d9f04e13
Revises: b5e1c8a3f7d2
Create Date: 2026-07-13 13:37:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision: str = "c7a2d9f04e13"
down_revision: str | None = "b5e1c8a3f7d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    op.add_column("courses", sa.Column("content", sa.Text(), nullable=True))
    op.drop_index("ix_course_modules_course_id", table_name="course_modules")
    op.drop_table("course_modules")


def downgrade() -> None:
    """Откат миграции."""
    op.create_table(
        "course_modules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_course_modules_course_id", "course_modules", ["course_id"])
    op.drop_column("courses", "content")
