"""Human-readable admin labels for order rows (avoids misleading raw enum combinations)."""

from __future__ import annotations

from enum import StrEnum

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.models.order import Order


class AdminOrderLifecycleKind(StrEnum):
    ACTIVE_TEMPORARY_HOLD = "active_temporary_hold"
    EXPIRED_UNPAID_HOLD = "expired_unpaid_hold"
    CONFIRMED_PAID = "confirmed_paid"
    OTHER = "other"


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

    if bs == BookingStatus.CONFIRMED and ps == PaymentStatus.PAID:
        return (
            AdminOrderLifecycleKind.CONFIRMED_PAID,
            "Confirmed booking — payment received.",
        )

    return (
        AdminOrderLifecycleKind.OTHER,
        f"Other state (booking={bs.value}, payment={ps.value}, cancellation={cs.value}).",
    )
