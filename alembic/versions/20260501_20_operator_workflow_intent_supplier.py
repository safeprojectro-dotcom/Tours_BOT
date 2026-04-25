"""Y37.5: add need_supplier_offer to operator_workflow_intent enum.

Revision: 20260501_20
Revises: 20260430_19
"""

from __future__ import annotations

from alembic import op

revision = "20260501_20"
down_revision = "20260430_19"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE operator_workflow_intent ADD VALUE 'need_supplier_offer'")


def downgrade() -> None:
    raise NotImplementedError("PostgreSQL cannot remove enum values safely; restore from backup if needed.")
