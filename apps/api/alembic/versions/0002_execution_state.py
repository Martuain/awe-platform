"""persist build validation and preview execution state"""
from alembic import op
import sqlalchemy as sa

revision = "0002_execution_state"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "website_execution_states",
        sa.Column("project_id", sa.String(36), primary_key=True),
        sa.Column("generation_version", sa.Integer(), nullable=True),
        sa.Column("build_status", sa.String(32), nullable=True),
        sa.Column("build_result", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("validation_status", sa.String(32), nullable=True),
        sa.Column("validation_payload", sa.Text(), nullable=True),
        sa.Column("preview_status", sa.String(32), nullable=True),
        sa.Column("preview_payload", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

def downgrade():
    op.drop_table("website_execution_states")
