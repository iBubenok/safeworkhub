"""checklist items tree (parent_id, node_type)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-26 16:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

checklist_node_type = postgresql.ENUM("group", "item", name="checklist_node_type", create_type=False)


def upgrade() -> None:
    """Древовидные узлы чек-листа: parent_id + node_type; answer_type → nullable."""
    bind = op.get_bind()
    checklist_node_type.create(bind, checkfirst=True)

    op.add_column(
        "checklist_items",
        sa.Column("node_type", checklist_node_type, nullable=False, server_default="item"),
    )
    op.add_column(
        "checklist_items",
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_checklist_items_parent_id",
        "checklist_items",
        "checklist_items",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_checklist_items_parent_id", "checklist_items", ["parent_id"])
    op.alter_column("checklist_items", "answer_type", existing_type=sa.Enum(name="checklist_answer_type"), nullable=True)


def downgrade() -> None:
    op.alter_column("checklist_items", "answer_type", existing_type=sa.Enum(name="checklist_answer_type"), nullable=False)
    op.drop_index("ix_checklist_items_parent_id", table_name="checklist_items")
    op.drop_constraint("fk_checklist_items_parent_id", "checklist_items", type_="foreignkey")
    op.drop_column("checklist_items", "parent_id")
    op.drop_column("checklist_items", "node_type")
    bind = op.get_bind()
    checklist_node_type.drop(bind, checkfirst=True)
