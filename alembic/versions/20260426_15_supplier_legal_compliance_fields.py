"""Y2.1a: supplier legal/compliance identity fields.

Revision ID: 20260426_15
Revises: 20260425_14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260426_15"
down_revision = "20260425_14"
branch_labels = None
depends_on = None

supplier_legal_entity_type = postgresql.ENUM(
    "company",
    "individual_entrepreneur",
    "authorized_carrier",
    name="supplier_legal_entity_type",
)


def upgrade() -> None:
    supplier_legal_entity_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "suppliers",
        sa.Column("legal_entity_type", supplier_legal_entity_type, nullable=True),
    )
    op.add_column("suppliers", sa.Column("legal_registered_name", sa.String(length=255), nullable=True))
    op.add_column("suppliers", sa.Column("legal_registration_code", sa.String(length=128), nullable=True))
    op.add_column("suppliers", sa.Column("permit_license_type", sa.String(length=128), nullable=True))
    op.add_column("suppliers", sa.Column("permit_license_number", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("suppliers", "permit_license_number")
    op.drop_column("suppliers", "permit_license_type")
    op.drop_column("suppliers", "legal_registration_code")
    op.drop_column("suppliers", "legal_registered_name")
    op.drop_column("suppliers", "legal_entity_type")
    supplier_legal_entity_type.drop(op.get_bind(), checkfirst=True)
