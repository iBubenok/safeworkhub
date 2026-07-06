"""checklist visibility (org/public)

Revision ID: c9e3a70f5b12
Revises: b8d2f5a1c3e4
Create Date: 2026-07-06 14:44:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision: str = "c9e3a70f5b12"
down_revision: str | None = "b8d2f5a1c3e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    visibility = sa.Enum("org", "public", name="checklist_visibility")
    visibility.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "checklists",
        sa.Column("visibility", visibility, nullable=False, server_default="org"),
    )
    # Дальше значением управляет приложение.
    op.alter_column("checklists", "visibility", server_default=None)


def downgrade() -> None:
    """Откат миграции."""
    op.drop_column("checklists", "visibility")
    sa.Enum(name="checklist_visibility").drop(op.get_bind(), checkfirst=True)
