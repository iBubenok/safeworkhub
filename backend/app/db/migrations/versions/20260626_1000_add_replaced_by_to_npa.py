"""add replaced_by to npa

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-26 10:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Добавляет ссылку на акт-замену (supersedes) в деталь-таблицу npa."""
    op.add_column("npa", sa.Column("replaced_by_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_npa_replaced_by_id_materials",
        "npa",
        "materials",
        ["replaced_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_npa_replaced_by_id", "npa", ["replaced_by_id"])


def downgrade() -> None:
    """Удаляет ссылку на акт-замену."""
    op.drop_index("ix_npa_replaced_by_id", table_name="npa")
    op.drop_constraint("fk_npa_replaced_by_id_materials", "npa", type_="foreignkey")
    op.drop_column("npa", "replaced_by_id")
