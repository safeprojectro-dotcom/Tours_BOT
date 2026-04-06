"""Narrow admin order mutations — one explicit transition per entrypoint."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.models.order import Order
from app.repositories.order import OrderRepository
from app.repositories.tour import TourRepository


class AdminOrderNotFoundError(Exception):
    """No order row for the given id."""


class AdminOrderMarkCancelledByOperatorNotAllowedError(Exception):
    """Current order state does not allow operator cancellation via this slice."""

    def __init__(
        self,
        *,
        booking_status: str,
        payment_status: str,
        cancellation_status: str,
    ) -> None:
        self.booking_status = booking_status
        self.payment_status = payment_status
        self.cancellation_status = cancellation_status


class AdminOrderMarkDuplicateNotAllowedError(Exception):
    """Current order state does not allow duplicate-marking via this slice."""

    def __init__(
        self,
        *,
        booking_status: str,
        payment_status: str,
        cancellation_status: str,
    ) -> None:
        self.booking_status = booking_status
        self.payment_status = payment_status
        self.cancellation_status = cancellation_status


class AdminOrderMarkNoShowNotAllowedError(Exception):
    """Current order state or tour timing does not allow no-show marking via this slice."""

    def __init__(
        self,
        *,
        booking_status: str,
        payment_status: str,
        cancellation_status: str,
        reason: str | None = None,
    ) -> None:
        self.booking_status = booking_status
        self.payment_status = payment_status
        self.cancellation_status = cancellation_status
        self.reason = reason


class AdminOrderMarkReadyForDepartureNotAllowedError(Exception):
    """Current order state or tour timing does not allow ready-for-departure marking via this slice."""

    def __init__(
        self,
        *,
        booking_status: str,
        payment_status: str,
        cancellation_status: str,
        reason: str | None = None,
    ) -> None:
        self.booking_status = booking_status
        self.payment_status = payment_status
        self.cancellation_status = cancellation_status
        self.reason = reason


class AdminOrderWriteService:
    """
    Operator cancellation for an active temporary hold only (aligned with
    `AdminOrderLifecycleKind.ACTIVE_TEMPORARY_HOLD` / reservation expiry seat restore).

    Does not cancel paid bookings (no refund path). Does not touch payment rows or webhooks.

    Duplicate-marking (`mark_duplicate`) is allowed only for:
    - an **active temporary hold** (seat release same as expiry / operator cancel), or
    - an **expired unpaid hold** (seats already restored by expiry — only `cancellation_status` changes).
    Paid orders are rejected. No merge tooling.

    No-show (`mark_no_show`): **confirmed + paid + active cancellation** only, and only after
    **`tour.departure_datetime` is in the past** (post-departure manual terminal mark). Sets
    **`booking_status`/`cancellation_status` to `no_show`**; **does not** change **`payment_status`**,
    **does not** touch payment rows, **does not** adjust tour seats.

    Ready-for-departure (`mark_ready_for_departure`): **confirmed + paid + active cancellation** only,
    and only while **`tour.departure_datetime` is strictly in the future** (UTC). Updates
    **`booking_status` → `ready_for_departure` only**; **does not** change **`payment_status`** or
    **`cancellation_status`**, **does not** touch payment rows or seats.
    """

    def __init__(
        self,
        *,
        order_repository: OrderRepository | None = None,
        tour_repository: TourRepository | None = None,
    ) -> None:
        self._orders = order_repository or OrderRepository()
        self._tours = tour_repository or TourRepository()

    def mark_cancelled_by_operator(self, session: Session, *, order_id: int) -> Order:
        order = self._orders.get_for_update(session, order_id=order_id)
        if order is None:
            raise AdminOrderNotFoundError

        if order.cancellation_status == CancellationStatus.CANCELLED_BY_OPERATOR:
            return order

        if order.payment_status == PaymentStatus.PAID:
            raise AdminOrderMarkCancelledByOperatorNotAllowedError(
                booking_status=order.booking_status.value,
                payment_status=order.payment_status.value,
                cancellation_status=order.cancellation_status.value,
            )

        if self._is_active_temporary_hold(order):
            tour = self._tours.get_for_update(session, tour_id=order.tour_id)
            if tour is None:
                raise AdminOrderNotFoundError

            restored_seats = min(tour.seats_total, tour.seats_available + order.seats_count)
            self._tours.update(
                session,
                instance=tour,
                data={"seats_available": restored_seats},
            )
            return self._orders.update(
                session,
                instance=order,
                data={
                    "payment_status": PaymentStatus.UNPAID,
                    "cancellation_status": CancellationStatus.CANCELLED_BY_OPERATOR,
                    "reservation_expires_at": None,
                },
            )

        raise AdminOrderMarkCancelledByOperatorNotAllowedError(
            booking_status=order.booking_status.value,
            payment_status=order.payment_status.value,
            cancellation_status=order.cancellation_status.value,
        )

    def mark_duplicate(self, session: Session, *, order_id: int) -> Order:
        order = self._orders.get_for_update(session, order_id=order_id)
        if order is None:
            raise AdminOrderNotFoundError

        if order.cancellation_status == CancellationStatus.DUPLICATE:
            return order

        if order.payment_status == PaymentStatus.PAID:
            raise AdminOrderMarkDuplicateNotAllowedError(
                booking_status=order.booking_status.value,
                payment_status=order.payment_status.value,
                cancellation_status=order.cancellation_status.value,
            )

        if self._is_active_temporary_hold(order):
            tour = self._tours.get_for_update(session, tour_id=order.tour_id)
            if tour is None:
                raise AdminOrderNotFoundError

            restored_seats = min(tour.seats_total, tour.seats_available + order.seats_count)
            self._tours.update(
                session,
                instance=tour,
                data={"seats_available": restored_seats},
            )
            return self._orders.update(
                session,
                instance=order,
                data={
                    "payment_status": PaymentStatus.UNPAID,
                    "cancellation_status": CancellationStatus.DUPLICATE,
                    "reservation_expires_at": None,
                },
            )

        if self._is_expired_unpaid_hold(order):
            return self._orders.update(
                session,
                instance=order,
                data={"cancellation_status": CancellationStatus.DUPLICATE},
            )

        raise AdminOrderMarkDuplicateNotAllowedError(
            booking_status=order.booking_status.value,
            payment_status=order.payment_status.value,
            cancellation_status=order.cancellation_status.value,
        )

    def mark_no_show(self, session: Session, *, order_id: int, now: datetime | None = None) -> Order:
        current = now or datetime.now(UTC)
        order = self._orders.get_for_update(session, order_id=order_id)
        if order is None:
            raise AdminOrderNotFoundError

        if (
            order.booking_status == BookingStatus.NO_SHOW
            and order.cancellation_status == CancellationStatus.NO_SHOW
        ):
            return order

        tour = self._tours.get(session, order.tour_id)
        if tour is None:
            raise AdminOrderNotFoundError

        if not self._is_eligible_confirmed_paid_active(order):
            raise AdminOrderMarkNoShowNotAllowedError(
                booking_status=order.booking_status.value,
                payment_status=order.payment_status.value,
                cancellation_status=order.cancellation_status.value,
            )

        if tour.departure_datetime >= current:
            raise AdminOrderMarkNoShowNotAllowedError(
                booking_status=order.booking_status.value,
                payment_status=order.payment_status.value,
                cancellation_status=order.cancellation_status.value,
                reason="departure_not_in_past",
            )

        return self._orders.update(
            session,
            instance=order,
            data={
                "booking_status": BookingStatus.NO_SHOW,
                "cancellation_status": CancellationStatus.NO_SHOW,
            },
        )

    def mark_ready_for_departure(
        self,
        session: Session,
        *,
        order_id: int,
        now: datetime | None = None,
    ) -> Order:
        """
        Narrow pre-departure mark: **confirmed + paid + active cancellation**, tour departure
        **strictly after** `now` (UTC). Idempotent when already **`ready_for_departure`** with paid+active.
        """
        current = now or datetime.now(UTC)
        order = self._orders.get_for_update(session, order_id=order_id)
        if order is None:
            raise AdminOrderNotFoundError

        if (
            order.booking_status == BookingStatus.READY_FOR_DEPARTURE
            and order.payment_status == PaymentStatus.PAID
            and order.cancellation_status == CancellationStatus.ACTIVE
        ):
            return order

        if not self._is_eligible_confirmed_paid_active(order):
            raise AdminOrderMarkReadyForDepartureNotAllowedError(
                booking_status=order.booking_status.value,
                payment_status=order.payment_status.value,
                cancellation_status=order.cancellation_status.value,
            )

        tour = self._tours.get(session, order.tour_id)
        if tour is None:
            raise AdminOrderNotFoundError

        if tour.departure_datetime <= current:
            raise AdminOrderMarkReadyForDepartureNotAllowedError(
                booking_status=order.booking_status.value,
                payment_status=order.payment_status.value,
                cancellation_status=order.cancellation_status.value,
                reason="departure_not_in_future",
            )

        return self._orders.update(
            session,
            instance=order,
            data={"booking_status": BookingStatus.READY_FOR_DEPARTURE},
        )

    @staticmethod
    def _is_eligible_confirmed_paid_active(order: Order) -> bool:
        return (
            order.booking_status == BookingStatus.CONFIRMED
            and order.payment_status == PaymentStatus.PAID
            and order.cancellation_status == CancellationStatus.ACTIVE
        )

    @staticmethod
    def _is_active_temporary_hold(order) -> bool:
        return (
            order.booking_status == BookingStatus.RESERVED
            and order.payment_status == PaymentStatus.AWAITING_PAYMENT
            and order.cancellation_status == CancellationStatus.ACTIVE
            and order.reservation_expires_at is not None
        )

    @staticmethod
    def _is_expired_unpaid_hold(order) -> bool:
        return (
            order.booking_status == BookingStatus.RESERVED
            and order.payment_status == PaymentStatus.UNPAID
            and order.cancellation_status == CancellationStatus.CANCELLED_NO_PAYMENT
        )
