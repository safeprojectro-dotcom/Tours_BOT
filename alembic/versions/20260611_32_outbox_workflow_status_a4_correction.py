"""A4 correction: business-specific workflow_status values + DB default draft.

Revision: 20260611_32
Revises: 20260610_31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260611_32"
down_revision = "20260610_31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE supplier_clarification_outbox_items SET workflow_status = 'draft' "
            "WHERE workflow_status = 'open'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE supplier_clarification_outbox_items SET workflow_status = 'cancelled' "
            "WHERE workflow_status = 'dismissed'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE supplier_clarification_outbox_items SET workflow_status = 'sent_externally_later' "
            "WHERE workflow_status = 'done'"
        )
    )
    op.drop_constraint(
        "ck_supplier_clarification_outbox_items_workflow_status",
        "supplier_clarification_outbox_items",
        type_="check",
    )
    op.create_check_constraint(
        "ck_supplier_clarification_outbox_items_workflow_status",
        "supplier_clarification_outbox_items",
        "workflow_status IN ('draft', 'ready_for_review', 'cancelled', 'sent_externally_later')",
    )
    op.alter_column(
        "supplier_clarification_outbox_items",
        "workflow_status",
        server_default=sa.text("'draft'"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE supplier_clarification_outbox_items SET workflow_status = 'open' "
            "WHERE workflow_status = 'draft'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE supplier_clarification_outbox_items SET workflow_status = 'dismissed' "
            "WHERE workflow_status = 'cancelled'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE supplier_clarification_outbox_items SET workflow_status = 'done' "
            "WHERE workflow_status IN ('ready_for_review', 'sent_externally_later')"
        )
    )
    op.drop_constraint(
        "ck_supplier_clarification_outbox_items_workflow_status",
        "supplier_clarification_outbox_items",
        type_="check",
    )
    op.create_check_constraint(
        "ck_supplier_clarification_outbox_items_workflow_status",
        "supplier_clarification_outbox_items",
        "workflow_status IN ('open', 'done', 'dismissed')",
    )
    op.alter_column(
        "supplier_clarification_outbox_items",
        "workflow_status",
        server_default=sa.text("'open'"),
        existing_nullable=False,
    )
