"""Track 5a: commercial resolution selection (no order bridge).

Revision ID: 20260422_11
Revises: 20260421_10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260422_11"
down_revision = "20260421_10"
branch_labels = None
depends_on = None

commercial_kind_create = postgresql.ENUM(
    "assisted_closure",
    "external_record",
    name="commercial_resolution_kind",
    create_type=True,
)

commercial_kind = postgresql.ENUM(
    "assisted_closure",
    "external_record",
    name="commercial_resolution_kind",
    create_type=False,
)


def upgrade() -> None:
    # PostgreSQL: ADD VALUE cannot always run inside a transaction (pre-PG 15 patterns).
    for val in ("under_review", "supplier_selected", "closed_assisted", "closed_external"):
        with op.get_context().autocommit_block():
            op.execute(sa.text(f"ALTER TYPE custom_marketplace_request_status ADD VALUE '{val}'"))

    op.execute(
        sa.text(
            "UPDATE custom_marketplace_requests SET status = 'closed_assisted'::custom_marketplace_request_status "
            "WHERE status::text = 'fulfilled'"
        )
    )

    bind = op.get_bind()
    commercial_kind_create.create(bind, checkfirst=True)

    op.add_column(
        "custom_marketplace_requests",
        sa.Column(
            "selected_supplier_response_id",
            sa.Integer(),
            sa.ForeignKey("supplier_custom_request_responses.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "custom_marketplace_requests",
        sa.Column("commercial_resolution_kind", commercial_kind, nullable=True),
    )
    op.create_index(
        op.f("ix_custom_marketplace_requests_selected_supplier_response_id"),
        "custom_marketplace_requests",
        ["selected_supplier_response_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_custom_marketplace_requests_selected_supplier_response_id"),
        table_name="custom_marketplace_requests",
    )
    op.drop_column("custom_marketplace_requests", "commercial_resolution_kind")
    op.drop_column("custom_marketplace_requests", "selected_supplier_response_id")
    bind = op.get_bind()
    commercial_kind_create.drop(bind, checkfirst=True)
    # custom_marketplace_request_status enum values are not removed (PostgreSQL limitation).
