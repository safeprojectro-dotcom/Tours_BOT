"""Add operator assignment columns to custom_marketplace_requests (Y36.2)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260429_18"
down_revision = "20260428_17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "custom_marketplace_requests",
        sa.Column("assigned_operator_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "custom_marketplace_requests",
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "custom_marketplace_requests",
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_custom_marketplace_requests_assigned_operator_id",
        "custom_marketplace_requests",
        "users",
        ["assigned_operator_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_custom_marketplace_requests_assigned_by_user_id",
        "custom_marketplace_requests",
        "users",
        ["assigned_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_custom_marketplace_requests_assigned_operator_id",
        "custom_marketplace_requests",
        ["assigned_operator_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_custom_marketplace_requests_assigned_operator_id", table_name="custom_marketplace_requests")
    op.drop_constraint(
        "fk_custom_marketplace_requests_assigned_by_user_id",
        "custom_marketplace_requests",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_custom_marketplace_requests_assigned_operator_id",
        "custom_marketplace_requests",
        type_="foreignkey",
    )
    op.drop_column("custom_marketplace_requests", "assigned_at")
    op.drop_column("custom_marketplace_requests", "assigned_by_user_id")
    op.drop_column("custom_marketplace_requests", "assigned_operator_id")
