"""create checklists and checklist items

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-26 12:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

checklist_status = postgresql.ENUM("draft", "published", "archived", name="checklist_status", create_type=False)
checklist_answer_type = postgresql.ENUM(
    "compliance", "yes_no", "text", "number", name="checklist_answer_type", create_type=False
)


def upgrade() -> None:
    """Создаёт таблицы чек-листов и их пунктов + enum-типы."""
    bind = op.get_bind()
    checklist_status.create(bind, checkfirst=True)
    checklist_answer_type.create(bind, checkfirst=True)

    op.create_table(
        "checklists",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", checklist_status, nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checklists_org", "checklists", ["organization_id"])
    op.create_index("ix_checklists_status", "checklists", ["status"])

    op.create_table(
        "checklist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checklist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("answer_type", checklist_answer_type, nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column("reference_material_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["checklist_id"], ["checklists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reference_material_id"], ["materials.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checklist_items_checklist_id", "checklist_items", ["checklist_id"])


def downgrade() -> None:
    """Удаляет таблицы чек-листов и enum-типы."""
    op.drop_index("ix_checklist_items_checklist_id", table_name="checklist_items")
    op.drop_table("checklist_items")
    op.drop_index("ix_checklists_status", table_name="checklists")
    op.drop_index("ix_checklists_org", table_name="checklists")
    op.drop_table("checklists")
    bind = op.get_bind()
    checklist_answer_type.drop(bind, checkfirst=True)
    checklist_status.drop(bind, checkfirst=True)
