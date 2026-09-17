"""CAP-037 deployment lifecycle current/previous semantics.

Revision ID: 0010_deployment_lifecycle
Revises: 0009_execution_state_merge
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_deployment_lifecycle"
down_revision = "0009_execution_state_merge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "website_deployments",
        sa.Column("lifecycle_role", sa.String(length=32), nullable=False, server_default="historical"),
    )
    op.add_column(
        "website_deployments",
        sa.Column("snapshot_ref", sa.String(length=500), nullable=True),
    )
    op.create_index(
        "ix_website_deployments_lifecycle_role",
        "website_deployments",
        ["lifecycle_role"],
        unique=False,
    )

    # Existing CAP-036 deployments already have durable snapshots named from
    # deployment ID. Make that identity observable without changing snapshots.
    op.execute("""
        UPDATE website_deployments
        SET snapshot_ref = 'awe-deployment-' || id
        WHERE status IN ('deployed', 'stopped')
          AND snapshot_ref IS NULL
    """)

    # Reconstruct current/previous from successful deployment chronology.
    # Failed/queued/deploying rows remain historical.
    op.execute("""
        WITH ranked AS (
            SELECT id,
                   project_id,
                   ROW_NUMBER() OVER (
                       PARTITION BY project_id
                       ORDER BY COALESCE(deployed_at, created_at) DESC, version DESC
                   ) AS rn
            FROM website_deployments
            WHERE status IN ('deployed', 'stopped')
        )
        UPDATE website_deployments d
        SET lifecycle_role = CASE
            WHEN r.rn = 1 THEN 'current'
            WHEN r.rn = 2 THEN 'previous'
            ELSE 'historical'
        END
        FROM ranked r
        WHERE d.id = r.id
    """)

    op.create_index(
        "uq_website_deployments_one_current",
        "website_deployments",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("lifecycle_role = 'current'"),
    )


def downgrade() -> None:
    op.drop_index("uq_website_deployments_one_current", table_name="website_deployments")
    op.drop_index("ix_website_deployments_lifecycle_role", table_name="website_deployments")
    op.drop_column("website_deployments", "snapshot_ref")
    op.drop_column("website_deployments", "lifecycle_role")
