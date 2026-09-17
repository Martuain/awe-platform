"""initial MVP schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-04
"""
from alembic import op
from app.store import Base

INITIAL_TABLES = [
    "projects",
    "discovery_sessions",
    "context_versions",
    "website_strategies",
    "website_strategy_versions",
    "brand_design_directions",
    "brand_design_direction_versions",
    "website_specifications",
    "website_generations",
    "website_deployments",
    "website_generation_versions",
    "website_specification_versions",
    "source_messages",
]

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    metadata = Base.metadata
    tables = [metadata.tables[name] for name in INITIAL_TABLES]
    for table in tables:
        table.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    metadata = Base.metadata
    for name in reversed(INITIAL_TABLES):
        metadata.tables[name].drop(op.get_bind(), checkfirst=True)
