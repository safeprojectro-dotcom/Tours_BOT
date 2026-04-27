from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.repositories.base import SQLAlchemyRepository


class SupplierOfferTourBridgeRepository(SQLAlchemyRepository[SupplierOfferTourBridge]):
    def __init__(self) -> None:
        super().__init__(SupplierOfferTourBridge)

    def get_active_for_offer(self, session: Session, *, supplier_offer_id: int) -> SupplierOfferTourBridge | None:
        stmt = select(SupplierOfferTourBridge).where(
            SupplierOfferTourBridge.supplier_offer_id == supplier_offer_id,
            SupplierOfferTourBridge.status == "active",
        )
        return session.scalar(stmt)
