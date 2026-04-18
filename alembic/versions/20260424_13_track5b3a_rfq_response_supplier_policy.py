"""Track 5b.3a: supplier-declared commercial policy on RFQ responses.

Revision ID: 20260424_13
Revises: 20260423_12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260424_13"
down_revision = "20260423_12"
branch_labels = None
depends_on = None

tour_sales_mode = postgresql.ENUM(
    "per_seat",
    "full_bus",
    name="tour_sales_mode",
    create_type=False,
)

supplier_offer_payment_mode = postgresql.ENUM(
    "platform_checkout",
    "assisted_closure",
    name="supplier_offer_payment_mode",
    create_type=False,
)


def upgrade() -> None:
    op.add_column(
        "supplier_custom_request_responses",
        sa.Column(
            "supplier_declared_sales_mode",
            tour_sales_mode,
            nullable=True,
        ),
    )
    op.add_column(
        "supplier_custom_request_responses",
        sa.Column(
            "supplier_declared_payment_mode",
            supplier_offer_payment_mode,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("supplier_custom_request_responses", "supplier_declared_payment_mode")
    op.drop_column("supplier_custom_request_responses", "supplier_declared_sales_mode")
