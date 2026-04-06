"""Read-only move *readiness* hints for admin order detail (Phase 6 / Step 28).

Does not authorize or perform moves — decision-support only for future narrow move slices.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.models.enums import CancellationStatus, PaymentStatus
from app.models.order import Order
from app.services.admin_order_lifecycle import AdminOrderLifecycleKind
from app.services.admin_order_payment_visibility import AdminPaymentCorrectionVisibility


@dataclass(frozen=True)
class AdminMoveReadinessResult:
    can_consider_move: bool
    move_blockers: tuple[str, ...]
    move_readiness_hint: str


def compute_move_readiness(
    *,
    order: Order,
    lifecycle_kind: AdminOrderLifecycleKind,
    correction: AdminPaymentCorrectionVisibility,
    open_handoff_count: int,
    now: datetime | None = None,
) -> AdminMoveReadinessResult:
    """
    Conservative: only `confirmed_paid` or `ready_for_departure_paid` + paid + active cancellation
    + future departure + no payment ambiguity + no open handoffs → *consider* future move work.

    Any doubt → blockers populated; `can_consider_move` is False.
    """
    current = now or datetime.now(UTC)
    blockers: list[str] = []

    if correction.needs_manual_review:
        blockers.append("payment_correction_manual_review")
    if open_handoff_count > 0:
        blockers.append("open_handoff_open")
    if order.payment_status != PaymentStatus.PAID:
        blockers.append("order_not_paid")
    if order.cancellation_status != CancellationStatus.ACTIVE:
        blockers.append("cancellation_not_active")
    if lifecycle_kind not in (
        AdminOrderLifecycleKind.CONFIRMED_PAID,
        AdminOrderLifecycleKind.READY_FOR_DEPARTURE_PAID,
    ):
        blockers.append("lifecycle_not_move_candidate")

    tour = order.tour
    if tour is not None and tour.departure_datetime <= current:
        blockers.append("tour_departure_not_in_future")

    unique = tuple(blockers)

    if not unique:
        hint = (
            "Persisted data is consistent enough that a future narrow move-to-tour/date "
            "feature could be considered for this order; no move exists yet and this is not "
            "an authorization to move."
        )
        return AdminMoveReadinessResult(
            can_consider_move=True,
            move_blockers=(),
            move_readiness_hint=hint,
        )

    hint = (
        "Move-to-tour/date work is not advised from persisted data alone until blockers are "
        f"addressed: {', '.join(unique)}."
    )
    return AdminMoveReadinessResult(
        can_consider_move=False,
        move_blockers=unique,
        move_readiness_hint=hint,
    )
