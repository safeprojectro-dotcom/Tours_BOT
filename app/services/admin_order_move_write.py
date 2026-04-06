"""Narrow admin order move mutation (Phase 6 / Step 29).

Cross-tour or same-tour boarding change only when Step 28 move-readiness passes.
Does not mutate payment rows; does not change booking/payment enums except `tour_id` / `boarding_point_id`.
`total_amount` is intentionally unchanged (reconcile price offline if needed).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import TourStatus
from app.models.order import Order
from app.models.tour import BoardingPoint, Tour
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.tour import TourRepository
from app.services.admin_order_lifecycle import describe_order_admin_lifecycle
from app.services.admin_order_move_readiness import compute_move_readiness
from app.services.admin_order_payment_visibility import compute_payment_correction_visibility
from app.services.admin_order_write import AdminOrderNotFoundError


class AdminOrderMoveNotAllowedError(Exception):
    """Move rejected — readiness, target validation, or seat safety."""

    def __init__(self, *, code: str, message: str | None = None) -> None:
        self.code = code
        self.message = message or code


class AdminOrderMoveWriteService:
    """
    `POST /admin/orders/{order_id}/move` — requires Step 28-style readiness (`can_consider_move`).

    - **Cross-tour:** restore seats on source tour, deduct on target; `tour_id` + `boarding_point_id` updated.
    - **Same tour, different boarding:** update `boarding_point_id` only (no seat change).
    - **Same tour + same boarding:** idempotent no-op.

    Target tour must be **`open_for_sale`**, **`departure_datetime > now`**, **`currency`** must match order.
    No payment-row writes; **`total_amount`** unchanged by policy.
    """

    def __init__(
        self,
        *,
        order_repository: OrderRepository | None = None,
        tour_repository: TourRepository | None = None,
        payment_repository: PaymentRepository | None = None,
    ) -> None:
        self._orders = order_repository or OrderRepository()
        self._tours = tour_repository or TourRepository()
        self._payments = payment_repository or PaymentRepository()

    def move_order(
        self,
        session: Session,
        *,
        order_id: int,
        target_tour_id: int,
        target_boarding_point_id: int,
        now: datetime | None = None,
    ) -> Order:
        current = now or datetime.now(UTC)
        order = self._orders.get_by_id_for_admin_detail_for_update(session, order_id=order_id)
        if order is None or order.tour is None or order.boarding_point is None:
            raise AdminOrderNotFoundError

        all_payments = self._payments.list_by_order(session, order_id=order.id)
        correction = compute_payment_correction_visibility(order, all_payments)
        lifecycle_kind, _ = describe_order_admin_lifecycle(order)
        open_handoff_count = sum(1 for h in order.handoffs if h.status == "open")
        readiness = compute_move_readiness(
            order=order,
            lifecycle_kind=lifecycle_kind,
            correction=correction,
            open_handoff_count=open_handoff_count,
            now=current,
        )
        if not readiness.can_consider_move:
            raise AdminOrderMoveNotAllowedError(
                code="order_move_not_ready",
                message=",".join(readiness.move_blockers),
            )

        if session.get(Tour, target_tour_id) is None:
            raise AdminOrderMoveNotAllowedError(code="order_move_target_tour_not_found")

        bp = session.get(BoardingPoint, target_boarding_point_id)
        if bp is None or bp.tour_id != target_tour_id:
            raise AdminOrderMoveNotAllowedError(
                code="order_move_boarding_not_on_target_tour",
            )

        if target_tour_id == order.tour_id and target_boarding_point_id == order.boarding_point_id:
            return order

        if target_tour_id == order.tour_id:
            return self._orders.update(
                session,
                instance=order,
                data={"boarding_point_id": target_boarding_point_id},
            )

        source_tid = order.tour_id
        tid_low, tid_high = (source_tid, target_tour_id) if source_tid < target_tour_id else (target_tour_id, source_tid)
        first = self._tours.get_for_update(session, tour_id=tid_low)
        second = self._tours.get_for_update(session, tour_id=tid_high)
        if first is None or second is None:
            raise AdminOrderMoveNotAllowedError(code="order_move_target_tour_not_found")
        source_tour = first if first.id == source_tid else second
        target_tour = first if first.id == target_tour_id else second

        self._validate_target_tour(target_tour, order=order, now=current)

        if target_tour.seats_available < order.seats_count:
            raise AdminOrderMoveNotAllowedError(code="order_move_insufficient_seats_on_target")

        restored_source = min(
            source_tour.seats_total,
            source_tour.seats_available + order.seats_count,
        )
        new_target_available = target_tour.seats_available - order.seats_count
        if new_target_available < 0:
            raise AdminOrderMoveNotAllowedError(code="order_move_insufficient_seats_on_target")

        self._tours.update(
            session,
            instance=source_tour,
            data={"seats_available": restored_source},
        )
        self._tours.update(
            session,
            instance=target_tour,
            data={"seats_available": new_target_available},
        )
        return self._orders.update(
            session,
            instance=order,
            data={
                "tour_id": target_tour_id,
                "boarding_point_id": target_boarding_point_id,
            },
        )

    @staticmethod
    def _validate_target_tour(target: Tour, *, order: Order, now: datetime) -> None:
        if target.status != TourStatus.OPEN_FOR_SALE:
            raise AdminOrderMoveNotAllowedError(code="order_move_target_tour_not_open_for_sale")
        if target.departure_datetime <= now:
            raise AdminOrderMoveNotAllowedError(code="order_move_target_departure_not_in_future")
        if target.currency != order.currency:
            raise AdminOrderMoveNotAllowedError(code="order_move_currency_mismatch")
        if target.sales_deadline is not None and target.sales_deadline < now:
            raise AdminOrderMoveNotAllowedError(code="order_move_target_sales_deadline_passed")
