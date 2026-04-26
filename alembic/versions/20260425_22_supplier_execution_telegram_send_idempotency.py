"""Y50: idempotency rows for outbound Telegram send on a supplier execution attempt (no other behavior).

Revision: 20260425_22
Revises: 20260502_21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260425_22"
down_revision = "20260502_21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_execution_attempt_telegram_idempotency",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplier_execution_attempt_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["supplier_execution_attempt_id"],
            ["supplier_execution_attempts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "supplier_execution_attempt_id",
            "idempotency_key",
            name="uq_ser_tg_idem_attempt_key",
        ),
        sa.CheckConstraint(
            "char_length(btrim(idempotency_key::text)) > 0",
            name="ck_ser_tg_idem_key_nonempty",
        ),
    )
    op.create_index(
        "ix_ser_tg_idem_attempt",
        "supplier_execution_attempt_telegram_idempotency",
        ["supplier_execution_attempt_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ser_tg_idem_attempt", table_name="supplier_execution_attempt_telegram_idempotency")
    op.drop_table("supplier_execution_attempt_telegram_idempotency")
