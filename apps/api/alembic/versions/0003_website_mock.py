"""add customer website mock and feedback lifecycle

Revision ID: 0003_website_mock
Revises: 0002_auth_security
"""
from alembic import op
from sqlalchemy import Column, DateTime, Integer, String, Text, inspect

revision = "0003_website_mock"
down_revision = "0002_auth_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "website_mocks" not in tables:
        op.create_table(
            "website_mocks",
            Column("id", String(36), primary_key=True),
            Column("project_id", String(36), nullable=False),
            Column("generation_version", Integer, nullable=False),
            Column("version", Integer, nullable=False),
            Column("status", String(32), nullable=False),
            Column("payload", Text, nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_website_mocks_project_id", "website_mocks", ["project_id"], unique=False)
    if "website_mock_versions" not in tables:
        op.create_table(
            "website_mock_versions",
            Column("id", String(36), primary_key=True),
            Column("project_id", String(36), nullable=False),
            Column("mock_id", String(36), nullable=False),
            Column("version", Integer, nullable=False),
            Column("status", String(32), nullable=False),
            Column("payload", Text, nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_website_mock_versions_project_id", "website_mock_versions", ["project_id"])
        op.create_index("ix_website_mock_versions_mock_id", "website_mock_versions", ["mock_id"])
    if "website_mock_feedback" not in tables:
        op.create_table(
            "website_mock_feedback",
            Column("id", String(36), primary_key=True),
            Column("project_id", String(36), nullable=False),
            Column("mock_id", String(36), nullable=False),
            Column("mock_version", Integer, nullable=False),
            Column("feedback", Text, nullable=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_website_mock_feedback_project_id", "website_mock_feedback", ["project_id"])
        op.create_index("ix_website_mock_feedback_mock_id", "website_mock_feedback", ["mock_id"])


def downgrade() -> None:
    op.drop_table("website_mock_feedback")
    op.drop_table("website_mock_versions")
    op.drop_table("website_mocks")
