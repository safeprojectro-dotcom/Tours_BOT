from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle, TourSalesMode, TourStatus
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository
from app.schemas.mini_app import (
    MiniAppSupplierOfferActionabilityState,
    MiniAppSupplierOfferLandingRead,
    MiniAppSupplierOfferPublicationContextRead,
)
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.tour_sales_mode_policy import TourSalesModePolicyService


class MiniAppSupplierOfferLandingService:
    """Read-only landing context for published supplier offers (Y30.1)."""

    def __init__(self) -> None:
        self._links = SupplierOfferExecutionLinkRepository()

    def _resolve_actionability(
        self,
        session: Session,
        *,
        offer: SupplierOffer,
    ) -> tuple[MiniAppSupplierOfferActionabilityState, str | None]:
        active = self._links.get_active_for_offer(session, supplier_offer_id=offer.id, for_update=False)
        if active is None:
            return MiniAppSupplierOfferActionabilityState.VIEW_ONLY, None
        tour = session.get(Tour, active.tour_id)
        if tour is None:
            return MiniAppSupplierOfferActionabilityState.VIEW_ONLY, None

        now = datetime.now(UTC)
        if tour.status != TourStatus.OPEN_FOR_SALE:
            return MiniAppSupplierOfferActionabilityState.VIEW_ONLY, tour.code
        if not tour_is_customer_catalog_visible(
            departure_datetime=tour.departure_datetime,
            sales_deadline=tour.sales_deadline,
            now=now,
        ):
            return MiniAppSupplierOfferActionabilityState.VIEW_ONLY, tour.code

        if tour.sales_mode == TourSalesMode.PER_SEAT:
            if tour.seats_available <= 0:
                return MiniAppSupplierOfferActionabilityState.SOLD_OUT, tour.code
            return MiniAppSupplierOfferActionabilityState.BOOKABLE, tour.code

        if tour.sales_mode == TourSalesMode.FULL_BUS:
            if tour.seats_available <= 0:
                return MiniAppSupplierOfferActionabilityState.SOLD_OUT, tour.code
            policy = TourSalesModePolicyService.policy_for_catalog_tour(tour)
            if policy.mini_app_catalog_reservation_allowed:
                return MiniAppSupplierOfferActionabilityState.BOOKABLE, tour.code
            if policy.operator_path_required:
                return MiniAppSupplierOfferActionabilityState.ASSISTED_ONLY, tour.code
            return MiniAppSupplierOfferActionabilityState.VIEW_ONLY, tour.code

        return MiniAppSupplierOfferActionabilityState.VIEW_ONLY, tour.code

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
        actionability_state, linked_tour_code = self._resolve_actionability(session, offer=row)
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
            actionability_state=actionability_state,
            linked_tour_code=linked_tour_code,
            publication=MiniAppSupplierOfferPublicationContextRead(
                lifecycle_status=row.lifecycle_status,
                published_at=row.published_at,
                showcase_chat_id=row.showcase_chat_id,
                showcase_message_id=row.showcase_message_id,
            ),
        )
