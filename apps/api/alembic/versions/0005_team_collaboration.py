"""add team roles and invitations

Revision ID: 0005_team_collaboration
Revises: 0004_website_mock_project_index
Create Date: 2026-09-07
"""
from alembic import op
from sqlalchemy import Column, DateTime, String, inspect, text

revision = "0005_team_collaboration"
down_revision = "0004_website_mock_project_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "team_members" not in tables:
        op.create_table(
            "team_members",
            Column("id", String(36), primary_key=True),
            Column("tenant_id", String(36), nullable=False),
            Column("user_id", String(36), nullable=False),
            Column("role", String(32), nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_team_members_tenant_id", "team_members", ["tenant_id"])
        op.create_index("ix_team_members_user_id", "team_members", ["user_id"])
    if "team_invitations" not in tables:
        op.create_table(
            "team_invitations",
            Column("id", String(36), primary_key=True),
            Column("tenant_id", String(36), nullable=False),
            Column("inviter_id", String(36), nullable=False),
            Column("email", String(320), nullable=False),
            Column("role", String(32), nullable=False),
            Column("token_hash", String(64), nullable=False),
            Column("status", String(32), nullable=False, server_default="pending"),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("expires_at", DateTime(timezone=True), nullable=False),
            Column("accepted_at", DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_team_invitations_tenant_id", "team_invitations", ["tenant_id"])
        op.create_index("ix_team_invitations_inviter_id", "team_invitations", ["inviter_id"])
        op.create_index("ix_team_invitations_email", "team_invitations", ["email"])
        op.create_index("ix_team_invitations_token_hash", "team_invitations", ["token_hash"], unique=True)
        op.create_index("ix_team_invitations_expires_at", "team_invitations", ["expires_at"])


def downgrade() -> None:
    op.drop_table("team_invitations")
    op.drop_table("team_members")
