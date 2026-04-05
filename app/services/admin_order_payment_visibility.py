"""Read-only payment correction hints for admin order detail (Phase 6 / Step 16).

Secondary to `lifecycle_kind` / `lifecycle_summary`; conservative flags derived from persisted rows only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models.enums import PaymentStatus
from app.models.order import Order
from app.models.payment import Payment


@dataclass(frozen=True)
class AdminPaymentCorrectionVisibility:
    payment_correction_hint: str | None
    needs_manual_review: bool
    payment_records_count: int
    latest_payment_status: PaymentStatus | None
    latest_payment_provider: str | None
    latest_payment_created_at: datetime | None
    has_multiple_payment_entries: bool
    has_paid_entry: bool
    has_awaiting_payment_entry: bool


def compute_payment_correction_visibility(
    order: Order,
    payments_newest_first: list[Payment],
) -> AdminPaymentCorrectionVisibility:
    """Derive correction-oriented visibility from order row + payment rows (newest first)."""
    count = len(payments_newest_first)
    latest = payments_newest_first[0] if payments_newest_first else None

    has_paid = any(p.status == PaymentStatus.PAID for p in payments_newest_first)
    has_awaiting = any(p.status == PaymentStatus.AWAITING_PAYMENT for p in payments_newest_first)

    hints: list[str] = []
    needs = False

    if count > 1:
        needs = True
        hints.append("Multiple payment entries; confirm which record matches operational truth.")

    if order.payment_status == PaymentStatus.PAID and not has_paid:
        needs = True
        hints.append("Order payment_status is paid but no payment row has status paid.")

    if has_paid and order.payment_status in (
        PaymentStatus.UNPAID,
        PaymentStatus.AWAITING_PAYMENT,
    ):
        needs = True
        hints.append("A paid payment row exists while order payment_status is not paid.")

    if count == 0 and order.payment_status == PaymentStatus.PAID:
        needs = True
        hints.append("Order payment_status is paid but there are no payment rows.")

    hint_str: str | None = " ".join(hints) if hints else None

    return AdminPaymentCorrectionVisibility(
        payment_correction_hint=hint_str,
        needs_manual_review=needs,
        payment_records_count=count,
        latest_payment_status=latest.status if latest else None,
        latest_payment_provider=latest.provider if latest else None,
        latest_payment_created_at=latest.created_at if latest else None,
        has_multiple_payment_entries=count > 1,
        has_paid_entry=has_paid,
        has_awaiting_payment_entry=has_awaiting,
    )
