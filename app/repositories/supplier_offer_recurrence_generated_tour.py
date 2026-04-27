from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.supplier_offer_recurrence_generated_tour import SupplierOfferRecurrenceGeneratedTour
from app.repositories.base import SQLAlchemyRepository


class SupplierOfferRecurrenceGeneratedTourRepository(SQLAlchemyRepository[SupplierOfferRecurrenceGeneratedTour]):
    def __init__(self) -> None:
        super().__init__(SupplierOfferRecurrenceGeneratedTour)

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
