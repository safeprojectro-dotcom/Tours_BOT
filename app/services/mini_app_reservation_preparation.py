from __future__ import annotations

from app.bot.services import PrivateReservationPreparationService
from app.models.enums import TourStatus
from app.schemas.mini_app import MiniAppReservationPreparationRead
from app.schemas.prepared import ReservationPreparationSummaryRead, ReservationPreparationTourRead
from app.services.catalog import CatalogLookupService
from sqlalchemy.orm import Session


class MiniAppReservationPreparationService:
    STATUS_SCOPE: tuple[TourStatus, ...] = (TourStatus.OPEN_FOR_SALE,)

    def __init__(
        self,
        *,
        catalog_lookup_service: CatalogLookupService | None = None,
        reservation_preparation_service: PrivateReservationPreparationService | None = None,
    ) -> None:
        self.catalog_lookup_service = catalog_lookup_service or CatalogLookupService()
        self.reservation_preparation_service = (
            reservation_preparation_service or PrivateReservationPreparationService()
        )

    def get_preparation(
        self,
        session: Session,
        *,
        code: str,
        language_code: str | None = None,
    ) -> MiniAppReservationPreparationRead | None:
        tour = self.catalog_lookup_service.get_tour_by_code(session, code=code)
        if tour is None or tour.status not in self.STATUS_SCOPE:
            return None

        detail = self.reservation_preparation_service.get_preparable_tour(
            session,
            tour_id=tour.id,
            language_code=language_code,
        )
        if detail is None:
            return None

        seat_count_options = list(self.reservation_preparation_service.list_seat_count_options(detail))
        return MiniAppReservationPreparationRead(
            tour=ReservationPreparationTourRead(
                id=detail.tour.id,
                code=detail.tour.code,
                departure_datetime=detail.tour.departure_datetime,
                return_datetime=detail.tour.return_datetime,
                base_price=detail.tour.base_price,
                currency=detail.tour.currency,
                seats_available_snapshot=detail.tour.seats_available,
                localized_content=detail.localized_content,
            ),
            boarding_points=detail.boarding_points,
            seat_count_options=seat_count_options,
        )

    def build_preparation_summary(
        self,
        session: Session,
        *,
        code: str,
        seats_count: int,
        boarding_point_id: int,
        language_code: str | None = None,
    ) -> ReservationPreparationSummaryRead | None:
        tour = self.catalog_lookup_service.get_tour_by_code(session, code=code)
        if tour is None or tour.status not in self.STATUS_SCOPE:
            return None

        return self.reservation_preparation_service.build_preparation_summary(
            session,
            tour_id=tour.id,
            seats_count=seats_count,
            boarding_point_id=boarding_point_id,
            language_code=language_code,
        )
