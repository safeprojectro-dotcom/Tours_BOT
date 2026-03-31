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
            "Hold released — not paid",
            "No payment was received before the deadline.",
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
                    "Temporary reservation expired",
                    "Payment was not completed before the hold ended.",
                    MiniAppBookingFacadeState.EXPIRED_TEMPORARY_RESERVATION,
                    MiniAppBookingPrimaryCta.BROWSE_TOURS,
                )
        return (
            "Temporary reservation (hold)",
            "Awaiting payment to confirm your seats.",
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


def _fallback_payment_phrase(status: PaymentStatus) -> str:
    mapping = {
        PaymentStatus.UNPAID: "Payment status: not paid.",
        PaymentStatus.AWAITING_PAYMENT: "Payment status: awaiting payment.",
        PaymentStatus.PAID: "Payment status: paid.",
        PaymentStatus.REFUNDED: "Payment status: refunded.",
        PaymentStatus.PARTIAL_REFUND: "Payment status: partial refund.",
    }
    return mapping.get(status, "See booking details below.")
