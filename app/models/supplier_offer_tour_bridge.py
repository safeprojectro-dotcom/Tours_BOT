"""B10: explicit admin bridge from supplier offer to Layer A Tour (no silent ORM, no auto-publish)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.supplier import SupplierOffer


class SupplierOfferTourBridge(TimestampMixin, Base):
    __tablename__ = "supplier_offer_tour_bridges"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'superseded', 'cancelled')", name="ck_sotb_status"),
        CheckConstraint(
            "bridge_kind IN ('created_new_tour', 'linked_existing_tour')",
            name="ck_sotb_bridge_kind",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_offer_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tour_id: Mapped[int] = mapped_column(
        ForeignKey("tours.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    bridge_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_packaging_status: Mapped[str] = mapped_column(String(64), nullable=False)
    source_lifecycle_status: Mapped[str] = mapped_column(String(64), nullable=False)
    packaging_snapshot_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier_offer: Mapped["SupplierOffer"] = relationship(back_populates="tour_bridges")
