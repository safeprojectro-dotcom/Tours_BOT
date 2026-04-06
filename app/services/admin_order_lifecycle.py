"""Human-readable admin labels for order rows (avoids misleading raw enum combinations)."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import and_, not_, or_

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.models.order import Order


class AdminOrderLifecycleKind(StrEnum):
    ACTIVE_TEMPORARY_HOLD = "active_temporary_hold"
    EXPIRED_UNPAID_HOLD = "expired_unpaid_hold"
    # Paid + active, post–Step 26 manual mark — read-side label only (not a mutation).
    READY_FOR_DEPARTURE_PAID = "ready_for_departure_paid"
    CONFIRMED_PAID = "confirmed_paid"
    OTHER = "other"


def sql_predicate_for_lifecycle_kind(kind: AdminOrderLifecycleKind):
    """
    WHERE fragment aligned with `describe_order_admin_lifecycle` classification
    (used for admin read-only list filtering — keep logic in sync).
    """
    expired = and_(
        Order.booking_status == BookingStatus.RESERVED,
        Order.payment_status == PaymentStatus.UNPAID,
        Order.cancellation_status == CancellationStatus.CANCELLED_NO_PAYMENT,
    )
    active_hold = and_(
        Order.booking_status == BookingStatus.RESERVED,
        Order.payment_status == PaymentStatus.AWAITING_PAYMENT,
        Order.cancellation_status == CancellationStatus.ACTIVE,
        Order.reservation_expires_at.is_not(None),
    )
    ready_for_departure_paid = and_(
        Order.booking_status == BookingStatus.READY_FOR_DEPARTURE,
        Order.payment_status == PaymentStatus.PAID,
        Order.cancellation_status == CancellationStatus.ACTIVE,
    )
    confirmed_paid = and_(
        Order.booking_status == BookingStatus.CONFIRMED,
        Order.payment_status == PaymentStatus.PAID,
    )
    classified = or_(expired, active_hold, ready_for_departure_paid, confirmed_paid)
    if kind == AdminOrderLifecycleKind.EXPIRED_UNPAID_HOLD:
        return expired
    if kind == AdminOrderLifecycleKind.ACTIVE_TEMPORARY_HOLD:
        return active_hold
    if kind == AdminOrderLifecycleKind.READY_FOR_DEPARTURE_PAID:
        return ready_for_departure_paid
    if kind == AdminOrderLifecycleKind.CONFIRMED_PAID:
        return confirmed_paid
    if kind == AdminOrderLifecycleKind.OTHER:
        return not_(classified)
    raise ValueError(f"Unsupported lifecycle kind: {kind!r}")


def describe_order_admin_lifecycle(order: Order) -> tuple[AdminOrderLifecycleKind, str]:
    """
    Map persisted order fields to a stable admin-facing summary.

    See docs/OPEN_QUESTIONS_AND_TECH_DEBT.md: expired unpaid holds may keep
    booking_status=reserved while cancellation_status=cancelled_no_payment.
    """
    bs, ps, cs = order.booking_status, order.payment_status, order.cancellation_status

    if (
        cs == CancellationStatus.CANCELLED_NO_PAYMENT
        and ps == PaymentStatus.UNPAID
        and bs == BookingStatus.RESERVED
    ):
        return (
            AdminOrderLifecycleKind.EXPIRED_UNPAID_HOLD,
            "Expired unpaid hold — cancelled for non-payment. Not an active reservation.",
        )

    if (
        bs == BookingStatus.RESERVED
        and ps == PaymentStatus.AWAITING_PAYMENT
        and cs == CancellationStatus.ACTIVE
        and order.reservation_expires_at is not None
    ):
        return (
            AdminOrderLifecycleKind.ACTIVE_TEMPORARY_HOLD,
            "Active temporary reservation — payment pending before deadline.",
        )

    if (
        bs == BookingStatus.READY_FOR_DEPARTURE
        and ps == PaymentStatus.PAID
        and cs == CancellationStatus.ACTIVE
    ):
        return (
            AdminOrderLifecycleKind.READY_FOR_DEPARTURE_PAID,
            "Paid booking — marked ready for departure (pre-trip).",
        )

    if bs == BookingStatus.CONFIRMED and ps == PaymentStatus.PAID:
        return (
            AdminOrderLifecycleKind.CONFIRMED_PAID,
            "Confirmed booking — payment received.",
        )

    return (
        AdminOrderLifecycleKind.OTHER,
        f"Other state (booking={bs.value}, payment={ps.value}, cancellation={cs.value}).",
    )
