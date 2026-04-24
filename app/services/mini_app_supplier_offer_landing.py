from __future__ import annotations

from dataclasses import dataclass
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
from app.schemas.tour_sales_mode_policy import CatalogActionabilityState
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.tour_sales_mode_policy import TourSalesModePolicyService


@dataclass(frozen=True)
class SupplierOfferLandingActionability:
    state: MiniAppSupplierOfferActionabilityState
    has_execution_link: bool
    linked_tour_id: int | None = None
    linked_tour_code: str | None = None


class MiniAppSupplierOfferLandingService:
    """Read-only landing context for published supplier offers (Y30.1)."""

    def __init__(self) -> None:
        self._links = SupplierOfferExecutionLinkRepository()

    def _resolve_actionability(
        self,
        session: Session,
        *,
        offer: SupplierOffer,
    ) -> SupplierOfferLandingActionability:
        active = self._links.get_active_for_offer(session, supplier_offer_id=offer.id, for_update=False)
        if active is None:
            return SupplierOfferLandingActionability(
                state=MiniAppSupplierOfferActionabilityState.VIEW_ONLY,
                has_execution_link=False,
            )
        tour = session.get(Tour, active.tour_id)
        if tour is None:
            return SupplierOfferLandingActionability(
                state=MiniAppSupplierOfferActionabilityState.UNAVAILABLE,
                has_execution_link=True,
            )

        now = datetime.now(UTC)
        if tour.status != TourStatus.OPEN_FOR_SALE:
            return SupplierOfferLandingActionability(
                state=MiniAppSupplierOfferActionabilityState.VIEW_ONLY,
                has_execution_link=True,
                linked_tour_id=tour.id,
                linked_tour_code=tour.code,
            )
        if not tour_is_customer_catalog_visible(
            departure_datetime=tour.departure_datetime,
            sales_deadline=tour.sales_deadline,
            now=now,
        ):
            return SupplierOfferLandingActionability(
                state=MiniAppSupplierOfferActionabilityState.VIEW_ONLY,
                has_execution_link=True,
                linked_tour_id=tour.id,
                linked_tour_code=tour.code,
            )

        if tour.sales_mode == TourSalesMode.PER_SEAT:
            if tour.seats_available <= 0:
                return SupplierOfferLandingActionability(
                    state=MiniAppSupplierOfferActionabilityState.SOLD_OUT,
                    has_execution_link=True,
                    linked_tour_id=tour.id,
                    linked_tour_code=tour.code,
                )
            return SupplierOfferLandingActionability(
                state=MiniAppSupplierOfferActionabilityState.BOOKABLE,
                has_execution_link=True,
                linked_tour_id=tour.id,
                linked_tour_code=tour.code,
            )

        if tour.sales_mode == TourSalesMode.FULL_BUS:
            policy = TourSalesModePolicyService.policy_for_catalog_tour(tour)
            if policy.catalog_actionability_state == CatalogActionabilityState.BOOKABLE:
                state = MiniAppSupplierOfferActionabilityState.BOOKABLE
            elif policy.catalog_actionability_state == CatalogActionabilityState.ASSISTED_ONLY:
                state = MiniAppSupplierOfferActionabilityState.ASSISTED_ONLY
            elif policy.catalog_actionability_state == CatalogActionabilityState.VIEW_ONLY:
                state = MiniAppSupplierOfferActionabilityState.VIEW_ONLY
            else:
                state = MiniAppSupplierOfferActionabilityState.UNAVAILABLE
            return SupplierOfferLandingActionability(
                state=state,
                has_execution_link=True,
                linked_tour_id=tour.id,
                linked_tour_code=tour.code,
            )

        return SupplierOfferLandingActionability(
            state=MiniAppSupplierOfferActionabilityState.UNAVAILABLE,
            has_execution_link=True,
            linked_tour_id=tour.id,
            linked_tour_code=tour.code,
        )

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
        actionability = self._resolve_actionability(session, offer=row)
        execution_cta_enabled = (
            actionability.state == MiniAppSupplierOfferActionabilityState.BOOKABLE
            and actionability.has_execution_link
            and actionability.linked_tour_id is not None
            and bool((actionability.linked_tour_code or "").strip())
        )
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
            actionability_state=actionability.state,
            has_execution_link=actionability.has_execution_link,
            linked_tour_id=actionability.linked_tour_id,
            linked_tour_code=actionability.linked_tour_code,
            execution_activation_available=execution_cta_enabled,
            execution_cta_enabled=execution_cta_enabled,
            execution_target_tour_code=actionability.linked_tour_code if execution_cta_enabled else None,
            fallback_cta=None if execution_cta_enabled else "browse_catalog",
            publication=MiniAppSupplierOfferPublicationContextRead(
                lifecycle_status=row.lifecycle_status,
                published_at=row.published_at,
                showcase_chat_id=row.showcase_chat_id,
                showcase_message_id=row.showcase_message_id,
            ),
        )
