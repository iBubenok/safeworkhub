"""checklist item references (multiple links per item)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-26 18:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Таблица ссылок пункта (1:много) + перенос старой одиночной ссылки."""
    op.create_table(
        "checklist_item_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["checklist_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checklist_item_references_item_id", "checklist_item_references", ["item_id"])

    # Бэкфилл: переносим существующую единственную ссылку в новую таблицу.
    op.execute(
        """
        INSERT INTO checklist_item_references (id, item_id, sort_order, material_id, note)
        SELECT gen_random_uuid(), id, 0, reference_material_id, reference_note
        FROM checklist_items
        WHERE reference_material_id IS NOT NULL OR reference_note IS NOT NULL
        """
    )

    # Старые одиночные поля больше не нужны (PG снимет FK с колонки автоматически).
    op.drop_column("checklist_items", "reference_material_id")
    op.drop_column("checklist_items", "reference_note")


def downgrade() -> None:
    """Возврат одиночной ссылки на пункт."""
    op.add_column("checklist_items", sa.Column("reference_note", sa.String(length=500), nullable=True))
    op.add_column(
        "checklist_items",
        sa.Column("reference_material_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_checklist_items_reference_material_id",
        "checklist_items",
        "materials",
        ["reference_material_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Возвращаем первую ссылку каждого пункта.
    op.execute(
        """
        UPDATE checklist_items ci
        SET reference_material_id = r.material_id, reference_note = r.note
        FROM checklist_item_references r
        WHERE r.item_id = ci.id AND r.sort_order = 0
        """
    )
    op.drop_index("ix_checklist_item_references_item_id", table_name="checklist_item_references")
    op.drop_table("checklist_item_references")
