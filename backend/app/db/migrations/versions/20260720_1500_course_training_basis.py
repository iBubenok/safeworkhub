"""course training basis fields

Revision ID: d8b3f1a45c26
Revises: c7a2d9f04e13
Create Date: 2026-07-20 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8b3f1a45c26"
down_revision: str | None = "c7a2d9f04e13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("training_basis", sa.String(length=500), nullable=True))
    op.add_column("courses", sa.Column("training_basis_url", sa.String(length=2000), nullable=True))


def downgrade() -> None:
    op.drop_column("courses", "training_basis_url")
    op.drop_column("courses", "training_basis")
