from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.repositories.order import OrderRepository
from app.repositories.tour import TourRepository

# Max orders processed per lazy call (catalog/prepare/booking paths); avoids unbounded work if backlog grows.
LAZY_EXPIRY_DEFAULT_LIMIT = 500


class ReservationExpiryService:
    def __init__(
        self,
        *,
        order_repository: OrderRepository | None = None,
        tour_repository: TourRepository | None = None,
    ) -> None:
        self.order_repository = order_repository or OrderRepository()
        self.tour_repository = tour_repository or TourRepository()

    def expire_due_reservations(
        self,
        session: Session,
        *,
        now: datetime | None = None,
        limit: int = 100,
    ) -> int:
        current_time = now or datetime.now(UTC)
        expired_count = 0
        order_ids = self.order_repository.list_expired_temporary_reservation_ids(
            session,
            now=current_time,
            limit=limit,
        )
        for order_id in order_ids:
            if self.expire_order_if_due(session, order_id=order_id, now=current_time):
                expired_count += 1
        return expired_count

    def expire_order_if_due(
        self,
        session: Session,
        *,
        order_id: int,
        now: datetime | None = None,
    ) -> bool:
        current_time = now or datetime.now(UTC)
        order = self.order_repository.get_for_update(session, order_id=order_id)
        if order is None or not self._is_eligible_for_expiry(order=order, now=current_time):
            return False

        tour = self.tour_repository.get_for_update(session, tour_id=order.tour_id)
        if tour is None:
            return False

        restored_seats = min(tour.seats_total, tour.seats_available + order.seats_count)
        self.tour_repository.update(
            session,
            instance=tour,
            data={"seats_available": restored_seats},
        )
        self.order_repository.update(
            session,
            instance=order,
            data={
                "payment_status": PaymentStatus.UNPAID,
                "cancellation_status": CancellationStatus.CANCELLED_NO_PAYMENT,
                "reservation_expires_at": None,
            },
        )
        return True

    @staticmethod
    def _is_eligible_for_expiry(*, order, now: datetime) -> bool:
        if order.booking_status != BookingStatus.RESERVED:
            return False
        if order.payment_status != PaymentStatus.AWAITING_PAYMENT:
            return False
        if order.cancellation_status != CancellationStatus.ACTIVE:
            return False
        if order.reservation_expires_at is None:
            return False
        if order.reservation_expires_at > now:
            return False
        return True


def lazy_expire_due_reservations(
    session: Session,
    *,
    now: datetime | None = None,
    limit: int = LAZY_EXPIRY_DEFAULT_LIMIT,
) -> int:
    """
    Release seats for expired temporary holds (AWAITING_PAYMENT + past reservation_expires_at).

    Safe to invoke on common read/write paths when no background worker runs: idempotent and bounded by ``limit``.
    """
    return ReservationExpiryService().expire_due_reservations(session, now=now, limit=limit)


def lazy_expire_due_reservations_commit_if_any(
    session: Session,
    *,
    now: datetime | None = None,
    limit: int = LAZY_EXPIRY_DEFAULT_LIMIT,
) -> int:
    """
    Run :func:`lazy_expire_due_reservations` and ``commit()`` when at least one order was expired.

    Use on **read-only** Mini App (and similar) handlers whose session would otherwise roll back
    on close without persisting seat release. Callers that already commit a wider transaction
    (e.g. hold creation, payment entry) should keep using :func:`lazy_expire_due_reservations`
    only so expiry stays in the same transaction as the rest of the flow.
    """
    n = lazy_expire_due_reservations(session, now=now, limit=limit)
    if n:
        session.commit()
    return n
