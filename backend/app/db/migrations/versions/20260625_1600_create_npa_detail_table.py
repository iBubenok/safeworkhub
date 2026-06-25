"""create npa detail table

Revision ID: f7081119aa01
Revises: e6f708111920
Create Date: 2026-06-25 16:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "f7081119aa01"
down_revision: str | None = "e6f708111920"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

act_kind = postgresql.ENUM(
    "federal_law",
    "constitutional_law",
    "code",
    "presidential_decree",
    "government_decree",
    "ministry_order",
    "gost",
    "sanpin",
    "sp",
    "regional_law",
    "municipal_act",
    "local_act",
    "other",
    name="npa_act_kind",
    create_type=False,
)
level = postgresql.ENUM("federal", "regional", "municipal", "local", name="npa_level", create_type=False)
act_status = postgresql.ENUM(
    "in_force",
    "not_in_force",
    "repealed",
    "amended",
    "suspended",
    name="npa_status",
    create_type=False,
)


def upgrade() -> None:
    """Создаёт деталь-таблицу НПА (1:1 к materials) и enum-типы."""
    bind = op.get_bind()
    act_kind.create(bind, checkfirst=True)
    level.create(bind, checkfirst=True)
    act_status.create(bind, checkfirst=True)

    op.create_table(
        "npa",
        sa.Column("material_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("act_kind", act_kind, nullable=False),
        sa.Column("level", level, nullable=True),
        sa.Column("act_status", act_status, nullable=True),
        sa.Column("document_number", sa.String(length=100), nullable=True),
        sa.Column("adoption_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("revision_date", sa.Date(), nullable=True),
        sa.Column("issuing_authority", sa.String(length=500), nullable=True),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("official_source_url", sa.String(length=2000), nullable=True),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("material_id"),
    )


def downgrade() -> None:
    """Удаляет деталь-таблицу НПА и enum-типы."""
    op.drop_table("npa")
    bind = op.get_bind()
    act_status.drop(bind, checkfirst=True)
    level.drop(bind, checkfirst=True)
    act_kind.drop(bind, checkfirst=True)
