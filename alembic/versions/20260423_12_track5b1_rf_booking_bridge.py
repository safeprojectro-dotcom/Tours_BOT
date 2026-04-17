"""Track 5b.1: RFQ booking bridge record (intent only; no orders/holds/payments).

Revision ID: 20260423_12
Revises: 20260422_11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260423_12"
down_revision = "20260422_11"
branch_labels = None
depends_on = None

bridge_status_create = postgresql.ENUM(
    "pending_validation",
    "ready",
    "linked_tour",
    "customer_notified",
    "superseded",
    "cancelled",
    name="custom_request_booking_bridge_status",
    create_type=True,
)

bridge_status = postgresql.ENUM(
    "pending_validation",
    "ready",
    "linked_tour",
    "customer_notified",
    "superseded",
    "cancelled",
    name="custom_request_booking_bridge_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    bridge_status_create.create(bind, checkfirst=True)

    op.create_table(
        "custom_request_booking_bridges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "request_id",
            sa.Integer(),
            sa.ForeignKey("custom_marketplace_requests.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "selected_supplier_response_id",
            sa.Integer(),
            sa.ForeignKey("supplier_custom_request_responses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "tour_id",
            sa.Integer(),
            sa.ForeignKey("tours.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("bridge_status", bridge_status, nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_custom_request_booking_bridges_request_id"),
        "custom_request_booking_bridges",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_custom_request_booking_bridges_tour_id"),
        "custom_request_booking_bridges",
        ["tour_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_custom_request_booking_bridges_tour_id"), table_name="custom_request_booking_bridges")
    op.drop_index(op.f("ix_custom_request_booking_bridges_request_id"), table_name="custom_request_booking_bridges")
    op.drop_table("custom_request_booking_bridges")
    bind = op.get_bind()
    bridge_status_create.drop(bind, checkfirst=True)
