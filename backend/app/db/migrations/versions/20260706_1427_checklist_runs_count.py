"""checklist runs_count counter

Revision ID: b8d2f5a1c3e4
Revises: a7c1e94b30df
Create Date: 2026-07-06 14:27:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision: str = "b8d2f5a1c3e4"
down_revision: str | None = "a7c1e94b30df"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    op.add_column(
        "checklists",
        sa.Column("runs_count", sa.Integer(), nullable=False, server_default="0"),
    )
    # Разовый бэкфилл: учитываем уже существующие проверки как использования.
    op.execute(
        "UPDATE checklists SET runs_count = ("
        "SELECT count(*) FROM checklist_runs WHERE checklist_runs.checklist_id = checklists.id"
        ")"
    )
    # Дальше значением управляет приложение (инкремент при старте проверки).
    op.alter_column("checklists", "runs_count", server_default=None)


def downgrade() -> None:
    """Откат миграции."""
    op.drop_column("checklists", "runs_count")
