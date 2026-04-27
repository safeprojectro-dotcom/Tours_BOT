from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourSalesMode, TourStatus
from app.repositories.order import OrderRepository
from app.repositories.tour import BoardingPointRepository, TourRepository
from app.schemas.order import OrderRead


class TemporaryReservationService:
    def __init__(
        self,
        *,
        order_repository: OrderRepository | None = None,
        tour_repository: TourRepository | None = None,
        boarding_point_repository: BoardingPointRepository | None = None,
    ) -> None:
        self.order_repository = order_repository or OrderRepository()
        self.tour_repository = tour_repository or TourRepository()
        self.boarding_point_repository = boarding_point_repository or BoardingPointRepository()

    def create_temporary_reservation(
        self,
        session: Session,
        *,
        user_id: int,
        tour_id: int,
        boarding_point_id: int,
        seats_count: int,
        source_channel: str | None,
        now: datetime | None = None,
    ) -> OrderRead | None:
        if seats_count <= 0:
            return None

        current_time = now or datetime.now(UTC)
        tour = self.tour_repository.get_for_update(session, tour_id=tour_id)
        if tour is None or tour.status != TourStatus.OPEN_FOR_SALE:
            return None
        if tour.seats_available < seats_count:
            return None

        boarding_point = self.boarding_point_repository.get(session, boarding_point_id)
        if boarding_point is None or boarding_point.tour_id != tour.id:
            return None

        reservation_expires_at = self.calculate_reservation_expiration(tour, now=current_time)
        if reservation_expires_at is None:
            return None

        updated_seats = tour.seats_available - seats_count
        self.tour_repository.update(
            session,
            instance=tour,
            data={"seats_available": updated_seats},
        )

        order = self.order_repository.create(
            session,
            data={
                "user_id": user_id,
                "tour_id": tour.id,
                "boarding_point_id": boarding_point.id,
                "seats_count": seats_count,
                "booking_status": BookingStatus.RESERVED,
                "payment_status": PaymentStatus.AWAITING_PAYMENT,
                "cancellation_status": CancellationStatus.ACTIVE,
                "reservation_expires_at": reservation_expires_at,
                "total_amount": (
                    tour.base_price
                    if tour.sales_mode is TourSalesMode.FULL_BUS
                    else tour.base_price * seats_count
                ),
                "currency": tour.currency,
                "source_channel": source_channel,
            },
        )
        return OrderRead.model_validate(order)

    def calculate_reservation_expiration(self, tour, *, now: datetime | None = None) -> datetime | None:
        current_time = now or datetime.now(UTC)
        if tour.departure_datetime <= current_time:
            return None

        ttl_minutes = get_settings().temp_reservation_ttl_minutes
        if ttl_minutes is not None:
            hold_window = timedelta(minutes=ttl_minutes)
        else:
            time_until_departure = tour.departure_datetime - current_time
            hold_window = (
                timedelta(hours=6) if time_until_departure <= timedelta(days=3) else timedelta(hours=24)
            )
        reservation_expires_at = current_time + hold_window

        if tour.sales_deadline is not None:
            if tour.sales_deadline <= current_time:
                return None
            reservation_expires_at = min(reservation_expires_at, tour.sales_deadline)

        if reservation_expires_at <= current_time:
            return None
        return reservation_expires_at
