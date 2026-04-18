"""User-visible booking/payment labels and CTA hints for Mini App (no business-rule duplication)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus
from app.schemas.mini_app import MiniAppBookingFacadeState, MiniAppBookingPrimaryCta
from app.schemas.order import OrderRead


def resolve_mini_app_booking_facade(order: OrderRead, *, now: datetime) -> tuple[str, str, MiniAppBookingFacadeState, MiniAppBookingPrimaryCta]:
    """
    Map persisted order state to short user-facing strings and a primary CTA for the detail screen.

    Expired hold after the expiry worker: reserved + unpaid + cancelled_no_payment (reservation_expires_at cleared).
    Expired hold before the worker runs: reserved + awaiting_payment + active + reservation_expires_at <= now.
    """
    o = order
    now_aware = now if now.tzinfo else now.replace(tzinfo=UTC)

    if (
        o.booking_status == BookingStatus.RESERVED
        and o.payment_status == PaymentStatus.UNPAID
        and o.cancellation_status == CancellationStatus.CANCELLED_NO_PAYMENT
    ):
        return (
            "Reservation expired",
            "This reservation closed without payment after the hold ended.",
            MiniAppBookingFacadeState.CANCELLED_NO_PAYMENT,
            MiniAppBookingPrimaryCta.BROWSE_TOURS,
        )

    if (
        o.booking_status == BookingStatus.RESERVED
        and o.payment_status == PaymentStatus.AWAITING_PAYMENT
        and o.cancellation_status == CancellationStatus.ACTIVE
    ):
        exp = o.reservation_expires_at
        if exp is not None:
            end = exp if exp.tzinfo else exp.replace(tzinfo=UTC)
            if end <= now_aware:
                return (
                    "Reservation expired",
                    "The payment deadline passed before checkout was completed.",
                    MiniAppBookingFacadeState.EXPIRED_TEMPORARY_RESERVATION,
                    MiniAppBookingPrimaryCta.BROWSE_TOURS,
                )
        return (
            "Reserved temporarily",
            "Payment pending — complete checkout to confirm your seats.",
            MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION,
            MiniAppBookingPrimaryCta.PAY_NOW,
        )

    if o.booking_status == BookingStatus.CONFIRMED and o.payment_status == PaymentStatus.PAID:
        return (
            "Confirmed",
            "Paid — your booking is confirmed.",
            MiniAppBookingFacadeState.CONFIRMED,
            MiniAppBookingPrimaryCta.BACK_TO_BOOKINGS,
        )

    if o.booking_status in (
        BookingStatus.READY_FOR_DEPARTURE,
        BookingStatus.IN_PROGRESS,
        BookingStatus.COMPLETED,
    ):
        labels = {
            BookingStatus.READY_FOR_DEPARTURE: ("Getting ready to depart", "Your trip is coming up."),
            BookingStatus.IN_PROGRESS: ("Tour in progress", "Enjoy your trip."),
            BookingStatus.COMPLETED: ("Tour completed", "Thank you for traveling with us."),
        }
        b, p = labels[o.booking_status]
        return (
            b,
            p,
            MiniAppBookingFacadeState.IN_TRIP_PIPELINE,
            MiniAppBookingPrimaryCta.BACK_TO_BOOKINGS,
        )

    if o.payment_status == PaymentStatus.PAID:
        return (
            "Confirmed",
            "Paid — your booking is confirmed.",
            MiniAppBookingFacadeState.CONFIRMED,
            MiniAppBookingPrimaryCta.BACK_TO_BOOKINGS,
        )

    return (
        "Booking update",
        _fallback_payment_phrase(o.payment_status),
        MiniAppBookingFacadeState.OTHER,
        MiniAppBookingPrimaryCta.BACK_TO_BOOKINGS,
    )


def format_payment_session_hint(*, status: PaymentStatus, provider: str) -> str:
    """Short hint for booking detail — human phrases only (no raw enum tokens)."""
    return f"Latest payment record: {_payment_status_phrase(status)} ({provider})."


def _payment_status_phrase(status: PaymentStatus) -> str:
    mapping = {
        PaymentStatus.UNPAID: "Not paid yet",
        PaymentStatus.AWAITING_PAYMENT: "Payment pending",
        PaymentStatus.PAID: "Paid",
        PaymentStatus.REFUNDED: "Refunded",
        PaymentStatus.PARTIAL_REFUND: "Partial refund",
    }
    return mapping.get(status, "Status update")


def _fallback_payment_phrase(status: PaymentStatus) -> str:
    return f"{_payment_status_phrase(status)} — see details below."
