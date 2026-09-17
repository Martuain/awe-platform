"""Merge durable execution state with the existing schema migration line.

Revision ID: 0009_execution_state_merge
Revises: 0008_website_content, 0002_execution_state

Both parent revisions may already be applied in an existing local database.
This merge is intentionally schema-neutral: it only gives Alembic one head so
application startup can continue using ``alembic upgrade head`` safely.
"""

from collections.abc import Sequence

from alembic import op  # noqa: F401 - standard Alembic revision surface

revision = "0009_execution_state_merge"
down_revision: tuple[str, str] = ("0008_website_content", "0002_execution_state")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
