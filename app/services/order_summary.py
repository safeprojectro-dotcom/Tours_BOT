from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.tour import BoardingPointRepository
from app.schemas.order import OrderRead
from app.schemas.prepared import OrderBoardingPointSummaryRead, OrderSummaryRead, OrderTourSummaryRead
from app.services.language_aware_tour import LanguageAwareTourReadService
from app.services.order_read import OrderReadService


class OrderSummaryService:
    def __init__(
        self,
        order_read_service: OrderReadService | None = None,
        language_aware_tour_service: LanguageAwareTourReadService | None = None,
        boarding_point_repository: BoardingPointRepository | None = None,
    ) -> None:
        self.order_read_service = order_read_service or OrderReadService()
        self.language_aware_tour_service = language_aware_tour_service or LanguageAwareTourReadService()
        self.boarding_point_repository = boarding_point_repository or BoardingPointRepository()

    def get_order_summary(
        self,
        session: Session,
        *,
        order_id: int,
        language_code: str | None = None,
    ) -> OrderSummaryRead | None:
        order = self.order_read_service.get_order(session, order_id=order_id)
        if order is None:
            return None
        return self._build_order_summary(session, order=order, language_code=language_code)

    def list_user_order_summaries(
        self,
        session: Session,
        *,
        user_id: int,
        language_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OrderSummaryRead]:
        orders = self.order_read_service.list_by_user(
            session,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        return [
            summary
            for order in orders
            if (summary := self._build_order_summary(session, order=order, language_code=language_code)) is not None
        ]

    def _build_order_summary(
        self,
        session: Session,
        *,
        order: OrderRead,
        language_code: str | None = None,
    ) -> OrderSummaryRead | None:
        prepared_tour = self.language_aware_tour_service.get_localized_tour_detail(
            session,
            tour_id=order.tour_id,
            language_code=language_code,
        )
        if prepared_tour is None:
            return None

        boarding_point = self.boarding_point_repository.get(session, order.boarding_point_id)
        boarding_point_summary = None
        if boarding_point is not None:
            boarding_point_summary = OrderBoardingPointSummaryRead(
                id=boarding_point.id,
                city=boarding_point.city,
                address=boarding_point.address,
                time=boarding_point.time,
                notes=boarding_point.notes,
            )

        return OrderSummaryRead(
            order=order,
            booking_status=order.booking_status,
            payment_status=order.payment_status,
            tour=OrderTourSummaryRead(
                id=prepared_tour.tour.id,
                code=prepared_tour.tour.code,
                departure_datetime=prepared_tour.tour.departure_datetime,
                return_datetime=prepared_tour.tour.return_datetime,
                sales_mode=prepared_tour.tour.sales_mode,
                localized_content=prepared_tour.localized_content,
            ),
            boarding_point=boarding_point_summary,
        )
