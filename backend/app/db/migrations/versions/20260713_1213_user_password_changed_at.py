"""user password_changed_at

Revision ID: b5e1c8a3f7d2
Revises: a4c7e51f92b0
Create Date: 2026-07-13 12:13:00.000000+00:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# Идентификаторы ревизии
revision: str = "b5e1c8a3f7d2"
down_revision: str | None = "a4c7e51f92b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Применение миграции."""
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    # Для существующих пользователей считаем, что пароль задан при создании.
    op.execute("UPDATE users SET password_changed_at = created_at WHERE password_changed_at IS NULL")


def downgrade() -> None:
    """Откат миграции."""
    op.drop_column("users", "password_changed_at")
