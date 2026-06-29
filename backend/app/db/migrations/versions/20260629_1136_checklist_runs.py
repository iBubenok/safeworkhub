"""checklist runs

Revision ID: 4fea8579dd5b
Revises: f6a7b8c9d0e1
Create Date: 2026-06-29 11:36:02.099491+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "4fea8579dd5b"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    op.create_table(
        "checklist_runs",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("checklist_id", sa.UUID(), nullable=True),
        sa.Column("checklist_title", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("conducted_by_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Enum("in_progress", "completed", name="checklist_run_status"), nullable=False),
        sa.Column("result", sa.Enum("passed", "has_issues", name="checklist_run_result"), nullable=True),
        sa.Column("gradable_count", sa.Integer(), nullable=False),
        sa.Column("compliant_count", sa.Integer(), nullable=False),
        sa.Column("non_compliant_count", sa.Integer(), nullable=False),
        sa.Column("not_applicable_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["checklist_id"], ["checklists.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conducted_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checklist_runs_org", "checklist_runs", ["organization_id"], unique=False)
    op.create_index("ix_checklist_runs_status", "checklist_runs", ["status"], unique=False)
    op.create_table(
        "checklist_run_answers",
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("group_title", sa.String(length=500), nullable=True),
        sa.Column("item_text", sa.Text(), nullable=False),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column(
            "answer_type",
            sa.Enum("compliance", "yes_no", "text", "number", name="checklist_run_answer_type"),
            nullable=False,
        ),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("references", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["checklist_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checklist_run_answers_run_id", "checklist_run_answers", ["run_id"], unique=False)


def downgrade() -> None:
    """Откат миграции."""
    op.drop_index("ix_checklist_run_answers_run_id", table_name="checklist_run_answers")
    op.drop_table("checklist_run_answers")
    op.drop_index("ix_checklist_runs_status", table_name="checklist_runs")
    op.drop_index("ix_checklist_runs_org", table_name="checklist_runs")
    op.drop_table("checklist_runs")
    op.execute("DROP TYPE IF EXISTS checklist_run_answer_type")
    op.execute("DROP TYPE IF EXISTS checklist_run_result")
    op.execute("DROP TYPE IF EXISTS checklist_run_status")
