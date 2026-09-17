"""add authentication, API keys, and project ownership

Revision ID: 0002_auth_security
Revises: 0001_initial_schema
Create Date: 2026-09-04
"""
from alembic import op
from sqlalchemy import Column, DateTime, String, Text, inspect, text

revision = "0002_auth_security"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

DEV_USER = "00000000-0000-0000-0000-000000000001"
DEV_TENANT = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("projects")}
    if "owner_id" not in columns:
        op.add_column("projects", Column("owner_id", String(36), nullable=True))
        bind.execute(text("UPDATE projects SET owner_id = :owner WHERE owner_id IS NULL"), {"owner": DEV_USER})
        op.alter_column("projects", "owner_id", nullable=False)
        op.create_index("ix_projects_owner_id", "projects", ["owner_id"])

    tables = set(inspector.get_table_names())
    if "users" not in tables:
        op.create_table(
            "users",
            Column("id", String(36), primary_key=True),
            Column("email", String(320), nullable=False),
            Column("password_hash", String(255), nullable=False),
            Column("tenant_id", String(36), nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)
        op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    if "auth_sessions" not in tables:
        op.create_table(
            "auth_sessions",
            Column("id", String(36), primary_key=True),
            Column("user_id", String(36), nullable=False),
            Column("token_hash", String(64), nullable=False),
            Column("expires_at", DateTime(timezone=True), nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
        op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
        op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    if "api_keys" not in tables:
        op.create_table(
            "api_keys",
            Column("id", String(36), primary_key=True),
            Column("user_id", String(36), nullable=False),
            Column("tenant_id", String(36), nullable=False),
            Column("name", String(120), nullable=False),
            Column("key_prefix", String(20), nullable=False),
            Column("key_hash", String(64), nullable=False),
            Column("scopes", Text, nullable=False, server_default="[]"),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("last_used_at", DateTime(timezone=True), nullable=True),
            Column("revoked_at", DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
        op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
        op.create_index("ix_api_keys_tenant_id", "api_keys", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("auth_sessions")
    op.drop_table("users")
    inspector = inspect(op.get_bind())
    if "owner_id" in {c["name"] for c in inspector.get_columns("projects")}:
        op.drop_index("ix_projects_owner_id", table_name="projects")
        op.drop_column("projects", "owner_id")
