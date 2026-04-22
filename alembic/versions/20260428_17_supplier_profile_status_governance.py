"""Y29.2: additive supplier profile status governance.

Revision ID: 20260428_17
Revises: 20260427_16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260428_17"
down_revision = "20260427_16"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE supplier_onboarding_status ADD VALUE IF NOT EXISTS 'suspended'")
    op.execute("ALTER TYPE supplier_onboarding_status ADD VALUE IF NOT EXISTS 'revoked'")
    op.add_column("suppliers", sa.Column("onboarding_suspension_reason", sa.Text(), nullable=True))
    op.add_column("suppliers", sa.Column("onboarding_revocation_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("suppliers", "onboarding_revocation_reason")
    op.drop_column("suppliers", "onboarding_suspension_reason")
