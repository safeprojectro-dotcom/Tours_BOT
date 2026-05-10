"""B13D: supplier_offer_showcase_publish_attempts — audit foundation (no live publish wiring).

Revision: 20260531_29
Revises: 20260530_28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260531_29"
down_revision = "20260530_28"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE supplier_offer_showcase_publish_attempt_status AS ENUM ("
        "'requested', 'provider_sent', 'persisted', 'failed'"
        ")"
    )
    op.execute(
        "CREATE TYPE supplier_offer_showcase_publish_actor_surface AS ENUM ("
        "'http_admin', 'telegram_bot'"
        ")"
    )

    attempt_status = postgresql.ENUM(
        "requested",
        "provider_sent",
        "persisted",
        "failed",
        name="supplier_offer_showcase_publish_attempt_status",
        create_type=False,
    )
    actor_surface = postgresql.ENUM(
        "http_admin",
        "telegram_bot",
        name="supplier_offer_showcase_publish_actor_surface",
        create_type=False,
    )

    op.create_table(
        "supplier_offer_showcase_publish_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplier_offer_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("channel_ref", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            attempt_status,
            server_default="requested",
            nullable=False,
        ),
        sa.Column("actor_surface", actor_surface, nullable=False),
        sa.Column("requested_by", sa.String(length=256), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("payload_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("showcase_chat_id", sa.String(length=64), nullable=True),
        sa.Column("showcase_message_id", sa.BigInteger(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retryable_failure", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["supplier_offer_id"],
            ["supplier_offers.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_supplier_offer_showcase_publish_attempts_supplier_offer_id"),
        "supplier_offer_showcase_publish_attempts",
        ["supplier_offer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_supplier_offer_showcase_publish_attempts_idempotency_key"),
        "supplier_offer_showcase_publish_attempts",
        ["idempotency_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_supplier_offer_showcase_publish_attempts_idempotency_key"),
        table_name="supplier_offer_showcase_publish_attempts",
    )
    op.drop_index(
        op.f("ix_supplier_offer_showcase_publish_attempts_supplier_offer_id"),
        table_name="supplier_offer_showcase_publish_attempts",
    )
    op.drop_table("supplier_offer_showcase_publish_attempts")
    op.execute("DROP TYPE IF EXISTS supplier_offer_showcase_publish_actor_surface")
    op.execute("DROP TYPE IF EXISTS supplier_offer_showcase_publish_attempt_status")
