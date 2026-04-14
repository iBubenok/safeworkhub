"""Add visibility to materials and articles.

Revision ID: 20260414_0001
Revises: 20251218_0001
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260414_0001"
down_revision = "20251218_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    visibility_enum = postgresql.ENUM(
        "org",
        "public",
        name="material_visibility",
    )
    visibility_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "materials",
        sa.Column(
            "visibility",
            visibility_enum,
            nullable=False,
            server_default="org",
        ),
    )

    op.create_index("ix_materials_visibility", "materials", ["visibility"])
    op.alter_column("materials", "visibility", server_default=None)

def downgrade() -> None:
    op.drop_index("ix_materials_visibility", table_name="materials")

    op.drop_column("materials", "visibility")

    visibility_enum = postgresql.ENUM(
        "org",
        "public",
        name="material_visibility",
    )
    visibility_enum.drop(op.get_bind(), checkfirst=True)
