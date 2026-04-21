"""Добавлены уведомления и настройки уведомлений."""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision: str = "b2f918ce7a5f"
down_revision: str | None = "20260414_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_notifications_table() -> None:
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def _create_notification_settings_table() -> None:
    op.create_table(
        "notification_settings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "enabled_categories",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text(
                '\'["check", "system", "reminder", "task"]\'::jsonb'
            ),
        ),
        sa.Column("in_app", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def upgrade() -> None:
    """Применение миграции."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "notifications" not in tables:
        _create_notifications_table()

    if "notifications" not in tables or not any(
        index["name"] == "idx_notifications_created_at"
        for index in inspector.get_indexes("notifications")
    ):
        op.create_index(
            "idx_notifications_created_at",
            "notifications",
            [sa.literal_column("created_at DESC")],
            unique=False,
        )

    if "notifications" not in tables or not any(
        index["name"] == "idx_notifications_user_id"
        for index in inspector.get_indexes("notifications")
    ):
        op.create_index(
            "idx_notifications_user_id",
            "notifications",
            ["user_id"],
            unique=False,
        )

    if "notifications" not in tables or not any(
        index["name"] == "idx_notifications_user_unread"
        for index in inspector.get_indexes("notifications")
    ):
        op.create_index(
            "idx_notifications_user_unread",
            "notifications",
            ["user_id", "is_read"],
            unique=False,
            postgresql_where=sa.text("(is_read = false)"),
        )

    if "notification_settings" not in tables:
        _create_notification_settings_table()


def downgrade() -> None:
    """Откат миграции."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "notifications" in tables:
        if any(index["name"] == "idx_notifications_user_unread" for index in inspector.get_indexes("notifications")):
            op.drop_index("idx_notifications_user_unread", table_name="notifications")
        if any(index["name"] == "idx_notifications_user_id" for index in inspector.get_indexes("notifications")):
            op.drop_index("idx_notifications_user_id", table_name="notifications")
        if any(index["name"] == "idx_notifications_created_at" for index in inspector.get_indexes("notifications")):
            op.drop_index("idx_notifications_created_at", table_name="notifications")
        op.drop_table("notifications")

    if "notification_settings" in tables:
        op.drop_table("notification_settings")
