from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle
from app.models.supplier import SupplierOffer
from app.schemas.mini_app import (
    MiniAppSupplierOfferLandingRead,
    MiniAppSupplierOfferPublicationContextRead,
)


class MiniAppSupplierOfferLandingService:
    """Read-only landing context for published supplier offers (Y30.1)."""

    def get_published_offer_landing(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
    ) -> MiniAppSupplierOfferLandingRead | None:
        row = session.get(SupplierOffer, supplier_offer_id)
        if row is None:
            return None
        if row.lifecycle_status != SupplierOfferLifecycle.PUBLISHED:
            return None
        return MiniAppSupplierOfferLandingRead(
            supplier_offer_id=row.id,
            title=row.title,
            description=row.description,
            departure_datetime=row.departure_datetime,
            return_datetime=row.return_datetime,
            boarding_places_text=row.boarding_places_text,
            transport_notes=row.transport_notes,
            vehicle_label=row.vehicle_label,
            seats_total=row.seats_total,
            base_price=row.base_price,
            currency=row.currency,
            publication=MiniAppSupplierOfferPublicationContextRead(
                lifecycle_status=row.lifecycle_status,
                published_at=row.published_at,
                showcase_chat_id=row.showcase_chat_id,
                showcase_message_id=row.showcase_message_id,
            ),
        )
