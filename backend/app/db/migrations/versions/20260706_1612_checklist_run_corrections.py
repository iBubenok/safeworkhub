"""checklist run corrections (reopen + per-field edit audit)

Revision ID: e2a6c1938b45
Revises: d1f4b8c206a7
Create Date: 2026-07-06 16:12:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision: str = "e2a6c1938b45"
down_revision: str | None = "d1f4b8c206a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    for table in ("checklist_runs", "checklist_run_answers"):
        op.add_column(table, sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("corrected_by_id", sa.UUID(), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_corrected_by_id_users",
            table,
            "users",
            ["corrected_by_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Откат миграции."""
    for table in ("checklist_run_answers", "checklist_runs"):
        op.drop_constraint(f"fk_{table}_corrected_by_id_users", table, type_="foreignkey")
        op.drop_column(table, "corrected_by_id")
        op.drop_column(table, "corrected_at")
