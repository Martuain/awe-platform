"""website content management foundation

Revision ID: 0008_website_content
Revises: 0007_sso
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_website_content"
down_revision = "0007_sso"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "website_content",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("page", sa.String(length=200), nullable=False),
        sa.Column("content_key", sa.String(length=200), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_website_content_project_id", "website_content", ["project_id"])
    op.create_index("uq_website_content_project_page_key", "website_content", ["project_id", "page", "content_key"], unique=True)
    op.create_table(
        "website_content_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("content_id", sa.String(length=36), nullable=False),
        sa.Column("page", sa.String(length=200), nullable=False),
        sa.Column("content_key", sa.String(length=200), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_website_content_versions_project_id", "website_content_versions", ["project_id"])
    op.create_index("ix_website_content_versions_content_id", "website_content_versions", ["content_id"])

def downgrade():
    op.drop_index("ix_website_content_versions_content_id", table_name="website_content_versions")
    op.drop_index("ix_website_content_versions_project_id", table_name="website_content_versions")
    op.drop_table("website_content_versions")
    op.drop_index("uq_website_content_project_page_key", table_name="website_content")
    op.drop_index("ix_website_content_project_id", table_name="website_content")
    op.drop_table("website_content")
