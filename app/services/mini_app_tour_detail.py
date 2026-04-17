from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import TourStatus
from app.schemas.mini_app import MiniAppTourDetailRead
from app.services.catalog import CatalogLookupService
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.language_aware_tour import LanguageAwareTourReadService
from app.services.reservation_expiry import lazy_expire_due_reservations
from app.services.tour_sales_mode_policy import TourSalesModePolicyService


class MiniAppTourDetailService:
    STATUS_SCOPE: tuple[TourStatus, ...] = (TourStatus.OPEN_FOR_SALE,)

    def __init__(
        self,
        *,
        catalog_lookup_service: CatalogLookupService | None = None,
        language_aware_tour_service: LanguageAwareTourReadService | None = None,
    ) -> None:
        self.catalog_lookup_service = catalog_lookup_service or CatalogLookupService()
        self.language_aware_tour_service = language_aware_tour_service or LanguageAwareTourReadService()

    def get_tour_detail(
        self,
        session: Session,
        *,
        code: str,
        language_code: str | None = None,
    ) -> MiniAppTourDetailRead | None:
        lazy_expire_due_reservations(session)
        tour = self.catalog_lookup_service.get_tour_by_code(session, code=code)
        if tour is None or tour.status not in self.STATUS_SCOPE:
            return None
        if not tour_is_customer_catalog_visible(
            departure_datetime=tour.departure_datetime,
            sales_deadline=tour.sales_deadline,
        ):
            return None

        detail = self.language_aware_tour_service.get_localized_tour_detail(
            session,
            tour_id=tour.id,
            language_code=language_code,
        )
        if detail is None:
            return None

        mode_policy = TourSalesModePolicyService.policy_for_sales_mode(detail.tour.sales_mode)
        return MiniAppTourDetailRead(
            tour=detail.tour,
            localized_content=detail.localized_content,
            boarding_points=detail.boarding_points,
            is_available=detail.tour.seats_available > 0,
            sales_mode_policy=mode_policy,
        )
