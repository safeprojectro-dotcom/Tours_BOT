"""S1C-2: supplier_notification_outbox delivery outcomes + Telegram audit columns.

Revision: 20260617_35
Revises: 20260617_34
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260617_35"
down_revision = "20260617_34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "supplier_notification_outbox",
        sa.Column("telegram_message_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "supplier_notification_outbox",
        sa.Column("last_delivery_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "supplier_notification_outbox",
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.drop_constraint("ck_supplier_notification_outbox_dispatch_status", "supplier_notification_outbox", type_="check")
    op.create_check_constraint(
        "ck_supplier_notification_outbox_dispatch_status",
        "supplier_notification_outbox",
        "dispatch_status IN ("
        "'pending_dispatch', 'skipped_no_target', 'delivery_in_progress', 'delivered', 'send_failed'"
        ")",
    )


def downgrade() -> None:
    op.drop_constraint("ck_supplier_notification_outbox_dispatch_status", "supplier_notification_outbox", type_="check")
    op.create_check_constraint(
        "ck_supplier_notification_outbox_dispatch_status",
        "supplier_notification_outbox",
        "dispatch_status IN ('pending_dispatch', 'skipped_no_target')",
    )
    op.drop_column("supplier_notification_outbox", "delivered_at")
    op.drop_column("supplier_notification_outbox", "last_delivery_error")
    op.drop_column("supplier_notification_outbox", "telegram_message_id")
