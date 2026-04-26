"""B4: store AI / deterministic packaging draft extras (admin-only read surface; no publish/AI in migration)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260527_25"
down_revision = "20260526_24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("supplier_offers", sa.Column("packaging_draft_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("supplier_offers", "packaging_draft_json")
