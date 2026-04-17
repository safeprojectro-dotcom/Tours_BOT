"""Track 4: custom request marketplace (Layer C; orders unchanged).

Revision ID: 20260421_10
Revises: 20260419_09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260421_10"
down_revision = "20260419_09"
branch_labels = None
depends_on = None

req_type_create = postgresql.ENUM(
    "group_trip",
    "custom_route",
    "other",
    name="custom_marketplace_request_type",
    create_type=True,
)

req_status_create = postgresql.ENUM(
    "open",
    "cancelled",
    "fulfilled",
    name="custom_marketplace_request_status",
    create_type=True,
)

req_source_create = postgresql.ENUM(
    "private_bot",
    "mini_app",
    name="custom_marketplace_request_source",
    create_type=True,
)

resp_kind_create = postgresql.ENUM(
    "declined",
    "proposed",
    name="supplier_custom_request_response_kind",
    create_type=True,
)

req_type = postgresql.ENUM(
    "group_trip",
    "custom_route",
    "other",
    name="custom_marketplace_request_type",
    create_type=False,
)

req_status = postgresql.ENUM(
    "open",
    "cancelled",
    "fulfilled",
    name="custom_marketplace_request_status",
    create_type=False,
)

req_source = postgresql.ENUM(
    "private_bot",
    "mini_app",
    name="custom_marketplace_request_source",
    create_type=False,
)

resp_kind = postgresql.ENUM(
    "declined",
    "proposed",
    name="supplier_custom_request_response_kind",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    req_type_create.create(bind, checkfirst=True)
    req_status_create.create(bind, checkfirst=True)
    req_source_create.create(bind, checkfirst=True)
    resp_kind_create.create(bind, checkfirst=True)

    op.create_table(
        "custom_marketplace_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_type", req_type, nullable=False),
        sa.Column("travel_date_start", sa.Date(), nullable=False),
        sa.Column("travel_date_end", sa.Date(), nullable=True),
        sa.Column("route_notes", sa.Text(), nullable=False),
        sa.Column("group_size", sa.Integer(), nullable=True),
        sa.Column("special_conditions", sa.Text(), nullable=True),
        sa.Column("source_channel", req_source, nullable=False),
        sa.Column("status", req_status, nullable=False),
        sa.Column("admin_intervention_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        op.f("ix_custom_marketplace_requests_user_id"),
        "custom_marketplace_requests",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_custom_marketplace_requests_status"),
        "custom_marketplace_requests",
        ["status"],
        unique=False,
    )

    op.create_table(
        "supplier_custom_request_responses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "request_id",
            sa.Integer(),
            sa.ForeignKey("custom_marketplace_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            sa.Integer(),
            sa.ForeignKey("suppliers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("response_kind", resp_kind, nullable=False),
        sa.Column("supplier_message", sa.Text(), nullable=True),
        sa.Column("quoted_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("quoted_currency", sa.String(length=8), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("request_id", "supplier_id", name="uq_supplier_response_per_request"),
    )
    op.create_index(
        op.f("ix_supplier_custom_request_responses_request_id"),
        "supplier_custom_request_responses",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_supplier_custom_request_responses_supplier_id"),
        "supplier_custom_request_responses",
        ["supplier_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_supplier_custom_request_responses_supplier_id"), table_name="supplier_custom_request_responses")
    op.drop_index(op.f("ix_supplier_custom_request_responses_request_id"), table_name="supplier_custom_request_responses")
    op.drop_table("supplier_custom_request_responses")
    op.drop_index(op.f("ix_custom_marketplace_requests_status"), table_name="custom_marketplace_requests")
    op.drop_index(op.f("ix_custom_marketplace_requests_user_id"), table_name="custom_marketplace_requests")
    op.drop_table("custom_marketplace_requests")
    bind = op.get_bind()
    resp_kind_create.drop(bind, checkfirst=True)
    req_source_create.drop(bind, checkfirst=True)
    req_status_create.drop(bind, checkfirst=True)
    req_type_create.drop(bind, checkfirst=True)
