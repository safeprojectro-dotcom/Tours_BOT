"""B8: optional audit link from template supplier offer → generated draft Tour (recurrence slice)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.supplier import SupplierOffer
    from app.models.tour import Tour


class SupplierOfferRecurrenceGeneratedTour(TimestampMixin, Base):
    """
    Records a draft `Tour` created by explicit admin recurrence generation.

    This is **not** `SupplierOfferTourBridge` — no automatic execution link or catalog activation.
    """

    __tablename__ = "supplier_offer_recurrence_generated_tours"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_supplier_offer_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tour_id: Mapped[int] = mapped_column(
        ForeignKey("tours.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)

    supplier_offer: Mapped["SupplierOffer"] = relationship(
        "SupplierOffer",
        foreign_keys=[source_supplier_offer_id],
        viewonly=True,
    )
    tour: Mapped["Tour"] = relationship(
        "Tour",
        foreign_keys=[tour_id],
        viewonly=True,
    )
