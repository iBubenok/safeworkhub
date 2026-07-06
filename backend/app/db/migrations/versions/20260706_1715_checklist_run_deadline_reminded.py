"""checklist run deadline_reminded_at (deadline reminder dedupe)

Revision ID: a4c7e51f92b0
Revises: f3b9d0c247e8
Create Date: 2026-07-06 17:15:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision: str = "a4c7e51f92b0"
down_revision: str | None = "f3b9d0c247e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    op.add_column("checklist_runs", sa.Column("deadline_reminded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Откат миграции."""
    op.drop_column("checklist_runs", "deadline_reminded_at")
