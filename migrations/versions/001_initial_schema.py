"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

import os

from alembic import op
import sqlalchemy as sa


revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _schema() -> str:
    return os.environ.get("APP_SCHEMA", "public")


def upgrade() -> None:
    schema = _schema()
    op.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    user_role = sa.Enum(
        "user",
        "institution",
        "moderator",
        "admin",
        name="user_role",
        schema=schema,
    )
    audience_type = sa.Enum(
        "high_schoolers",
        "university_students",
        "general_public",
        name="audience_type",
        schema=schema,
    )
    opportunity_type = sa.Enum(
        "internship",
        "job",
        "course",
        "volunteer",
        "event",
        name="opportunity_type",
        schema=schema,
    )
    opportunity_status = sa.Enum(
        "pending",
        "approved",
        "rejected",
        name="opportunity_status",
        schema=schema,
    )

    user_role.create(op.get_bind(), checkfirst=True)
    audience_type.create(op.get_bind(), checkfirst=True)
    opportunity_type.create(op.get_bind(), checkfirst=True)
    opportunity_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="user"),
        sa.Column("audience_type", audience_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema=schema,
    )

    op.create_table(
        "institutions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["owner_user_id"], [f"{schema}.users.id"]),
        schema=schema,
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
        schema=schema,
    )

    op.create_table(
        "opportunities",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("opportunity_type", opportunity_type, nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("submitted_by", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            opportunity_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("ai_tags", sa.JSON(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["category_id"], [f"{schema}.categories.id"]),
        sa.ForeignKeyConstraint(["institution_id"], [f"{schema}.institutions.id"]),
        sa.ForeignKeyConstraint(["submitted_by"], [f"{schema}.users.id"]),
        schema=schema,
    )

    op.create_table(
        "opportunity_audiences",
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("audience", audience_type, nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], [f"{schema}.opportunities.id"]),
        sa.PrimaryKeyConstraint("opportunity_id", "audience"),
        schema=schema,
    )

    op.create_table(
        "moderation_queue",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            opportunity_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["opportunity_id"], [f"{schema}.opportunities.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], [f"{schema}.users.id"]),
        sa.UniqueConstraint("opportunity_id"),
        schema=schema,
    )

    op.create_table(
        "saved_opportunities",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], [f"{schema}.users.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], [f"{schema}.opportunities.id"]),
        sa.PrimaryKeyConstraint("user_id", "opportunity_id"),
        schema=schema,
    )


def downgrade() -> None:
    schema = _schema()
    op.drop_table("saved_opportunities", schema=schema)
    op.drop_table("moderation_queue", schema=schema)
    op.drop_table("opportunity_audiences", schema=schema)
    op.drop_table("opportunities", schema=schema)
    op.drop_table("categories", schema=schema)
    op.drop_table("institutions", schema=schema)
    op.drop_table("users", schema=schema)

    opportunity_status = sa.Enum(
        "pending",
        "approved",
        "rejected",
        name="opportunity_status",
        schema=schema,
    )
    opportunity_type = sa.Enum(
        "internship",
        "job",
        "course",
        "volunteer",
        "event",
        name="opportunity_type",
        schema=schema,
    )
    audience_type = sa.Enum(
        "high_schoolers",
        "university_students",
        "general_public",
        name="audience_type",
        schema=schema,
    )
    user_role = sa.Enum(
        "user",
        "institution",
        "moderator",
        "admin",
        name="user_role",
        schema=schema,
    )

    opportunity_status.drop(op.get_bind(), checkfirst=True)
    opportunity_type.drop(op.get_bind(), checkfirst=True)
    audience_type.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
