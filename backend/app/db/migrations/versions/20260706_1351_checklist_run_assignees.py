"""checklist run assignees

Revision ID: a7c1e94b30df
Revises: 4fea8579dd5b
Create Date: 2026-07-06 13:51:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision: str = "a7c1e94b30df"
down_revision: str | None = "4fea8579dd5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    op.create_table(
        "checklist_run_assignees",
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["checklist_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("run_id", "user_id"),
    )
    op.create_index("ix_checklist_run_assignees_user_id", "checklist_run_assignees", ["user_id"])


def downgrade() -> None:
    """Откат миграции."""
    op.drop_index("ix_checklist_run_assignees_user_id", table_name="checklist_run_assignees")
    op.drop_table("checklist_run_assignees")
