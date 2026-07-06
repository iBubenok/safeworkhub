"""checklist run due_at (deadline)

Revision ID: f3b9d0c247e8
Revises: e2a6c1938b45
Create Date: 2026-07-06 16:43:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision: str = "f3b9d0c247e8"
down_revision: str | None = "e2a6c1938b45"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    op.add_column("checklist_runs", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Откат миграции."""
    op.drop_column("checklist_runs", "due_at")
