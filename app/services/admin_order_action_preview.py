"""Read-only suggested next-step preview for admin order detail (Phase 6 / Step 17).

Secondary to lifecycle_kind / lifecycle_summary and to payment correction hints.
Does not perform or authorize mutations — labels for operator orientation only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.services.admin_order_lifecycle import AdminOrderLifecycleKind
from app.services.admin_order_payment_visibility import AdminPaymentCorrectionVisibility


class AdminSuggestedAdminAction(StrEnum):
    """Conservative preview — prefer manual_review or none when unsure."""

    NONE = "none"
    MANUAL_REVIEW = "manual_review"
    HANDOFF_FOLLOW_UP = "handoff_follow_up"
    AWAIT_CUSTOMER_PAYMENT = "await_customer_payment"


@dataclass(frozen=True)
class AdminActionPreviewResult:
    suggested_admin_action: AdminSuggestedAdminAction
    allowed_admin_actions: tuple[str, ...]
    payment_action_preview: str | None


def _allowed_for(action: AdminSuggestedAdminAction) -> tuple[str, ...]:
    if action == AdminSuggestedAdminAction.MANUAL_REVIEW:
        return ("review_payment_records", "compare_order_payment_status_to_rows")
    if action == AdminSuggestedAdminAction.HANDOFF_FOLLOW_UP:
        return ("review_open_handoff",)
    if action == AdminSuggestedAdminAction.AWAIT_CUSTOMER_PAYMENT:
        return ("monitor_reservation_deadline",)
    return ()


def compute_admin_action_preview(
    *,
    lifecycle_kind: AdminOrderLifecycleKind,
    correction: AdminPaymentCorrectionVisibility,
    open_handoff_count: int,
) -> AdminActionPreviewResult:
    """
    Grounded only in lifecycle classification, correction visibility, and open handoff count.
    """
    if correction.needs_manual_review:
        return AdminActionPreviewResult(
            suggested_admin_action=AdminSuggestedAdminAction.MANUAL_REVIEW,
            allowed_admin_actions=_allowed_for(AdminSuggestedAdminAction.MANUAL_REVIEW),
            payment_action_preview=(
                "Payment records or order payment state look inconsistent; "
                "reconcile persisted rows before assuming operational truth."
            ),
        )

    if open_handoff_count > 0:
        return AdminActionPreviewResult(
            suggested_admin_action=AdminSuggestedAdminAction.HANDOFF_FOLLOW_UP,
            allowed_admin_actions=_allowed_for(AdminSuggestedAdminAction.HANDOFF_FOLLOW_UP),
            payment_action_preview=(
                "This order has an open handoff; operator follow-up may be appropriate."
            ),
        )

    if lifecycle_kind == AdminOrderLifecycleKind.ACTIVE_TEMPORARY_HOLD:
        return AdminActionPreviewResult(
            suggested_admin_action=AdminSuggestedAdminAction.AWAIT_CUSTOMER_PAYMENT,
            allowed_admin_actions=_allowed_for(AdminSuggestedAdminAction.AWAIT_CUSTOMER_PAYMENT),
            payment_action_preview=(
                "Reservation is active with payment pending; monitor until deadline or confirmation."
            ),
        )

    if lifecycle_kind == AdminOrderLifecycleKind.CONFIRMED_PAID:
        return AdminActionPreviewResult(
            suggested_admin_action=AdminSuggestedAdminAction.NONE,
            allowed_admin_actions=(),
            payment_action_preview="No payment follow-up suggested from current persisted data.",
        )

    if lifecycle_kind == AdminOrderLifecycleKind.EXPIRED_UNPAID_HOLD:
        return AdminActionPreviewResult(
            suggested_admin_action=AdminSuggestedAdminAction.NONE,
            allowed_admin_actions=(),
            payment_action_preview="Expired unpaid hold; no pending payment completion expected.",
        )

    # OTHER — uncommon combinations
    return AdminActionPreviewResult(
        suggested_admin_action=AdminSuggestedAdminAction.MANUAL_REVIEW,
        allowed_admin_actions=_allowed_for(AdminSuggestedAdminAction.MANUAL_REVIEW),
        payment_action_preview=(
            "Unusual booking/payment/cancellation combination; confirm state before acting."
        ),
    )
