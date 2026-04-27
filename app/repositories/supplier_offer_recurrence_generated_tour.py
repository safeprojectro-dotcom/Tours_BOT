from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.supplier_offer_recurrence_generated_tour import SupplierOfferRecurrenceGeneratedTour
from app.repositories.base import SQLAlchemyRepository


class SupplierOfferRecurrenceGeneratedTourRepository(SQLAlchemyRepository[SupplierOfferRecurrenceGeneratedTour]):
    def __init__(self) -> None:
        super().__init__(SupplierOfferRecurrenceGeneratedTour)

    def get_source_supplier_offer_id_for_tour(
        self,
        session: Session,
        *,
        tour_id: int,
    ) -> int | None:
        """If ``tour_id`` is a B8 recurrence-generated draft/instance, return the template offer id."""
        stmt = select(SupplierOfferRecurrenceGeneratedTour.source_supplier_offer_id).where(
            SupplierOfferRecurrenceGeneratedTour.tour_id == tour_id,
        )
        return session.scalar(stmt)

    def create(
        self,
        session: Session,
        *,
        source_supplier_offer_id: int,
        tour_id: int,
        sequence_index: int,
    ) -> SupplierOfferRecurrenceGeneratedTour:
        row = SupplierOfferRecurrenceGeneratedTour(
            source_supplier_offer_id=source_supplier_offer_id,
            tour_id=tour_id,
            sequence_index=sequence_index,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return row
