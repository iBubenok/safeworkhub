"""checklist option hints (per-answer editor hints)

Revision ID: d1f4b8c206a7
Revises: c9e3a70f5b12
Create Date: 2026-07-06 15:37:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "d1f4b8c206a7"
down_revision: str | None = "c9e3a70f5b12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    for table in ("checklist_items", "checklist_run_answers"):
        op.add_column(
            table,
            sa.Column("option_hints", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        )
        op.alter_column(table, "option_hints", server_default=None)


def downgrade() -> None:
    """Откат миграции."""
    op.drop_column("checklist_run_answers", "option_hints")
    op.drop_column("checklist_items", "option_hints")
