"""align website mock project index with revision history

Revision ID: 0004_website_mock_project_index
Revises: 0003_website_mock
"""
from alembic import op
from sqlalchemy import inspect

revision = "0004_website_mock_project_index"
down_revision = "0003_website_mock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    indexes = {idx["name"]: idx for idx in inspect(bind).get_indexes("website_mocks")}
    existing = indexes.get("ix_website_mocks_project_id")
    if existing and existing.get("unique"):
        op.drop_index("ix_website_mocks_project_id", table_name="website_mocks")
        op.create_index("ix_website_mocks_project_id", "website_mocks", ["project_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    indexes = {idx["name"]: idx for idx in inspect(bind).get_indexes("website_mocks")}
    existing = indexes.get("ix_website_mocks_project_id")
    if existing and not existing.get("unique"):
        op.drop_index("ix_website_mocks_project_id", table_name="website_mocks")
        op.create_index("ix_website_mocks_project_id", "website_mocks", ["project_id"], unique=True)
