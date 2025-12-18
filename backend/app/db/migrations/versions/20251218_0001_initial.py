"""Initial schema for SafeWorkHub MVP."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251218_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    material_type = postgresql.ENUM(
        "article",
        "npa",
        "template",
        "reference",
        "news",
        name="material_type",
    )
    material_status = postgresql.ENUM(
        "draft",
        "published",
        "archived",
        name="material_status",
    )
    subscription_status = postgresql.ENUM(
        "trial",
        "active",
        "past_due",
        "blocked",
        "expired",
        name="subscription_status",
    )
    course_assignment_status = postgresql.ENUM(
        "assigned",
        "in_progress",
        "completed",
        "overdue",
        name="course_assignment_status",
    )

    material_type.create(op.get_bind(), checkfirst=True)
    material_status.create(op.get_bind(), checkfirst=True)
    subscription_status.create(op.get_bind(), checkfirst=True)
    course_assignment_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("primary_organization_id", sa.Integer(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("inn", sa.String(length=12), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
    )

    op.create_foreign_key(
        "fk_users_primary_org",
        source_table="users",
        referent_table="organizations",
        local_cols=["primary_organization_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "tariffs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("price_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_yearly", sa.Numeric(10, 2), nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("tariff_id", sa.Integer(), sa.ForeignKey("tariffs.id"), nullable=False),
        sa.Column("status", subscription_status, nullable=False, server_default="trial"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "organization_users",
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("organization_id", "slug", name="uq_category_org_slug"),
    )

    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.String(length=1000), nullable=True),
        sa.Column("type", material_type, nullable=False, server_default="article"),
        sa.Column("status", material_status, nullable=False, server_default="draft"),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("views_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "setweight(to_tsvector('russian', coalesce(title, '')), 'A') || "
                "setweight(to_tsvector('russian', coalesce(summary, '')), 'B') || "
                "setweight(to_tsvector('russian', coalesce(content, '')), 'C')",
                persisted=True,
            ),
        ),
    )

    op.create_table(
        "refresh_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
    )

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
    )

    op.create_table(
        "course_modules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "course_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", course_assignment_status, nullable=False, server_default="assigned"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("course_id", "user_id", name="uq_course_assignment"),
    )

    # Индексы
    op.create_index("ix_users_email_lower", "users", ["email"])
    op.create_index("ix_users_primary_org", "users", ["primary_organization_id"])
    op.create_index("ix_organizations_inn", "organizations", ["inn"])
    op.create_index("ix_organizations_name", "organizations", ["name"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index("ix_subscriptions_valid_until", "subscriptions", ["valid_until"])
    op.create_index("ix_organization_users_user_id", "organization_users", ["user_id"])
    op.create_index("ix_organization_users_role", "organization_users", ["role"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_index("ix_categories_org", "categories", ["organization_id"])
    op.create_index("ix_categories_slug", "categories", ["slug"])
    op.create_index("ix_materials_type", "materials", ["type"])
    op.create_index("ix_materials_category_id", "materials", ["category_id"])
    op.create_index("ix_materials_published_at", "materials", ["published_at"])
    op.create_index("ix_materials_org", "materials", ["organization_id"])
    op.create_index(
        "ix_materials_search_vector",
        "materials",
        ["search_vector"],
        postgresql_using="gin",
    )
    op.create_index("ix_refresh_sessions_user", "refresh_sessions", ["user_id"])
    op.create_index("ix_refresh_sessions_family", "refresh_sessions", ["family_id"])
    op.create_index("ix_refresh_sessions_expires", "refresh_sessions", ["expires_at"])
    op.create_index("ix_audit_logs_org", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_user", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_courses_is_published", "courses", ["is_published"])
    op.create_index("ix_courses_org", "courses", ["organization_id"])
    op.create_index("ix_course_modules_course_id", "course_modules", ["course_id"])
    op.create_index("ix_course_assignments_org", "course_assignments", ["organization_id"])
    op.create_index("ix_course_assignments_status", "course_assignments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_course_assignments_status", table_name="course_assignments")
    op.drop_index("ix_course_assignments_org", table_name="course_assignments")
    op.drop_table("course_assignments")

    op.drop_index("ix_course_modules_course_id", table_name="course_modules")
    op.drop_table("course_modules")

    op.drop_index("ix_courses_org", table_name="courses")
    op.drop_index("ix_courses_is_published", table_name="courses")
    op.drop_table("courses")

    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user", table_name="audit_logs")
    op.drop_index("ix_audit_logs_org", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_refresh_sessions_expires", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_family", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_user", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")

    op.drop_index("ix_materials_search_vector", table_name="materials")
    op.drop_index("ix_materials_org", table_name="materials")
    op.drop_index("ix_materials_published_at", table_name="materials")
    op.drop_index("ix_materials_category_id", table_name="materials")
    op.drop_index("ix_materials_type", table_name="materials")
    op.drop_table("materials")

    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_index("ix_categories_org", table_name="categories")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_table("categories")

    op.drop_index("ix_organization_users_role", table_name="organization_users")
    op.drop_index("ix_organization_users_user_id", table_name="organization_users")
    op.drop_table("organization_users")

    op.drop_index("ix_subscriptions_valid_until", table_name="subscriptions")
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_index("ix_organizations_inn", table_name="organizations")
    op.drop_table("organizations")

    op.drop_index("ix_users_primary_org", table_name="users")
    op.drop_index("ix_users_email_lower", table_name="users")
    op.drop_table("users")

    op.drop_table("tariffs")

    op.execute("DROP TYPE IF EXISTS course_assignment_status")
    op.execute("DROP TYPE IF EXISTS subscription_status")
    op.execute("DROP TYPE IF EXISTS material_status")
    op.execute("DROP TYPE IF EXISTS material_type")
