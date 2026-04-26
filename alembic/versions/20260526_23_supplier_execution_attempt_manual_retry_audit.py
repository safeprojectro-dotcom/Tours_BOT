"""Y54: manual retry audit — link new attempt to original; reason; requester. No messaging in this migration.

Revision: 20260526_23
Revises: 20260425_22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260526_23"
down_revision = "20260425_22"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "supplier_execution_attempts",
        sa.Column("retry_from_supplier_execution_attempt_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "supplier_execution_attempts",
        sa.Column("retry_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "supplier_execution_attempts",
        sa.Column("retry_requested_by_user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_supplier_execution_attempts_retry_from_attempt",
        "supplier_execution_attempts",
        "supplier_execution_attempts",
        ["retry_from_supplier_execution_attempt_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_supplier_execution_attempts_retry_requested_by_user",
        "supplier_execution_attempts",
        "users",
        ["retry_requested_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_supplier_execution_attempts_retry_from",
        "supplier_execution_attempts",
        ["retry_from_supplier_execution_attempt_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_supplier_execution_attempts_retry_from", table_name="supplier_execution_attempts")
    op.drop_constraint(
        "fk_supplier_execution_attempts_retry_requested_by_user",
        "supplier_execution_attempts",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_supplier_execution_attempts_retry_from_attempt",
        "supplier_execution_attempts",
        type_="foreignkey",
    )
    op.drop_column("supplier_execution_attempts", "retry_requested_by_user_id")
    op.drop_column("supplier_execution_attempts", "retry_reason")
    op.drop_column("supplier_execution_attempts", "retry_from_supplier_execution_attempt_id")
