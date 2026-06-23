"""add deleted_at to notifications

Revision ID: 8ed3dc0a3dd2
Revises: b2f918ce7a5f
Create Date: 2026-06-23 19:22:17.647394+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Идентификаторы ревизии
revision: str = "8ed3dc0a3dd2"
down_revision: str | None = "b2f918ce7a5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Добавляет колонку мягкого удаления уведомлений."""
    op.add_column(
        "notifications",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Удаляет колонку мягкого удаления уведомлений."""
    op.drop_column("notifications", "deleted_at")
