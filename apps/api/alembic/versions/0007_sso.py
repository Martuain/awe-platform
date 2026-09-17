"""external SSO/OIDC identity and state boundary

Revision ID: 0007_sso
Revises: 0006_auth_recovery
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_sso"
down_revision = "0006_auth_recovery"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "sso_identities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sso_identities_user_id", "sso_identities", ["user_id"])
    op.create_index("ix_sso_identities_provider", "sso_identities", ["provider"])
    op.create_index("ix_sso_identities_subject", "sso_identities", ["subject"])
    op.create_index("ix_sso_identities_email", "sso_identities", ["email"])
    op.create_index("uq_sso_identity_provider_subject", "sso_identities", ["provider", "subject"], unique=True)
    op.create_table(
        "sso_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("nonce", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sso_states_state_hash", "sso_states", ["state_hash"], unique=True)
    op.create_index("ix_sso_states_expires_at", "sso_states", ["expires_at"])

def downgrade():
    op.drop_index("ix_sso_states_expires_at", table_name="sso_states")
    op.drop_index("ix_sso_states_state_hash", table_name="sso_states")
    op.drop_table("sso_states")
    op.drop_index("uq_sso_identity_provider_subject", table_name="sso_identities")
    op.drop_index("ix_sso_identities_email", table_name="sso_identities")
    op.drop_index("ix_sso_identities_subject", table_name="sso_identities")
    op.drop_index("ix_sso_identities_provider", table_name="sso_identities")
    op.drop_index("ix_sso_identities_user_id", table_name="sso_identities")
    op.drop_table("sso_identities")
