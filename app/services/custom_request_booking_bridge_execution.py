"""Track 5b.2: explicit RFQ bridge → Layer A preparation + temporary reservation (orchestration only)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import CustomRequestBookingBridgeStatus
from app.models.order import Order
from app.schemas.mini_app import MiniAppBridgeExecutionPreparationResponse, MiniAppBridgePaymentEligibilityRead
from app.schemas.prepared import OrderSummaryRead
from app.services.custom_request_booking_bridge_service import (
    BookingBridgeNotFoundError,
    BookingBridgeValidationError,
    CustomRequestBookingBridgeService,
)
from app.schemas.effective_commercial_execution_policy import EffectiveCommercialExecutionPolicyRead
from app.services.effective_commercial_execution_policy import EffectiveCommercialExecutionPolicyService
from app.services.mini_app_booking import MiniAppBookingService, MiniAppSelfServiceBookingNotAllowedError
from app.services.mini_app_reservation_preparation import MiniAppReservationPreparationService
from app.services.payment_entry import PaymentEntryService
from app.services.tour_sales_mode_policy import TourSalesModePolicyService


class BridgeExecutionBlocked(Exception):
    """Logical block (caller maps to HTTP) — not used when returning200 blocked envelope."""

    def __init__(self, *, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


# Customer-visible copy (English MVP — consistent with RFQ summaries)
_MSG_OPERATOR_ASSISTANCE = (
    "This tour is handled with team assistance. Please wait for our team to contact you about your request, "
    "or use the support option in the app."
)
_MSG_PREPARATION_UNAVAILABLE = (
    "Booking details cannot be loaded right now. The tour may have changed — please contact support."
)


def _execution_blocked_message(effective: EffectiveCommercialExecutionPolicyRead) -> str:
    if effective.blocked_code == "supplier_policy_incomplete":
        return (
            "This request is missing supplier commercial policy on the selected proposal. "
            "Please contact support so the team can update the supplier response."
        )
    if effective.blocked_code == "external_record":
        return "This request was closed outside the in-app booking flow."
    return _MSG_OPERATOR_ASSISTANCE


class CustomRequestBookingBridgeExecutionService:
    def __init__(
        self,
        *,
        bridge_service: CustomRequestBookingBridgeService | None = None,
        preparation_service: MiniAppReservationPreparationService | None = None,
        booking_service: MiniAppBookingService | None = None,
        payment_entry_service: PaymentEntryService | None = None,
    ) -> None:
        self._bridge = bridge_service or CustomRequestBookingBridgeService()
        self._preparation = preparation_service or MiniAppReservationPreparationService()
        self._booking = booking_service or MiniAppBookingService()
        self._payment_entry = payment_entry_service or PaymentEntryService()

    def get_execution_preparation(
        self,
        session: Session,
        *,
        request_id: int,
        telegram_user_id: int,
        language_code: str | None = None,
    ) -> MiniAppBridgeExecutionPreparationResponse:
        ctx = self._bridge.resolve_customer_execution_context(
            session,
            request_id=request_id,
            telegram_user_id=telegram_user_id,
        )
        policy = TourSalesModePolicyService.policy_for_tour(ctx.tour)
        effective = EffectiveCommercialExecutionPolicyService.resolve(
            tour=ctx.tour,
            request=ctx.request,
            response=ctx.response,
        )
        if not effective.self_service_preparation_allowed:
            return MiniAppBridgeExecutionPreparationResponse(
                self_service_available=False,
                blocked_code=effective.customer_blocked_code or effective.blocked_code,
                blocked_message=_execution_blocked_message(effective),
                preparation=None,
                tour_code=ctx.tour.code,
                sales_mode_policy=policy,
                effective_execution_policy=effective,
            )

        prep = self._preparation.get_preparation(
            session,
            code=ctx.tour.code,
            language_code=language_code,
        )
        if prep is None:
            return MiniAppBridgeExecutionPreparationResponse(
                self_service_available=False,
                blocked_code="tour_preparation_unavailable",
                blocked_message=_MSG_PREPARATION_UNAVAILABLE,
                preparation=None,
                tour_code=ctx.tour.code,
                sales_mode_policy=policy,
                effective_execution_policy=effective,
            )

        return MiniAppBridgeExecutionPreparationResponse(
            self_service_available=True,
            blocked_code=None,
            blocked_message=None,
            preparation=prep,
            tour_code=ctx.tour.code,
            sales_mode_policy=policy,
            effective_execution_policy=effective,
        )

    def create_execution_reservation(
        self,
        session: Session,
        *,
        request_id: int,
        telegram_user_id: int,
        seats_count: int,
        boarding_point_id: int | None,
        language_code: str | None = None,
    ) -> OrderSummaryRead:
        """Re-validates bridge context, enforces sales-mode policy, then existing Mini App hold path."""
        ctx = self._bridge.resolve_customer_execution_context(
            session,
            request_id=request_id,
            telegram_user_id=telegram_user_id,
        )
        effective = EffectiveCommercialExecutionPolicyService.resolve(
            tour=ctx.tour,
            request=ctx.request,
            response=ctx.response,
        )
        if not effective.self_service_hold_allowed:
            raise BridgeExecutionBlocked(
                code=effective.customer_blocked_code or effective.blocked_code or "execution_blocked",
                message=_execution_blocked_message(effective),
            )
        try:
            summary = self._booking.create_temporary_reservation(
                session,
                tour_code=ctx.tour.code,
                telegram_user_id=telegram_user_id,
                seats_count=seats_count,
                boarding_point_id=boarding_point_id,
                language_code=language_code,
            )
        except MiniAppSelfServiceBookingNotAllowedError as exc:
            raise BridgeExecutionBlocked(
                code=MiniAppSelfServiceBookingNotAllowedError.code,
                message="Self-service reservation is not available for this tour sales mode.",
            ) from exc
        if summary is None:
            raise BookingBridgeValidationError(
                "Temporary reservation could not be created. Check seats, boarding point, and sales window.",
            )
        if ctx.bridge.bridge_status != CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED:
            ctx.bridge.bridge_status = CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED
            session.add(ctx.bridge)
            session.flush()
        return summary

    def get_payment_eligibility(
        self,
        session: Session,
        *,
        request_id: int,
        telegram_user_id: int,
        order_id: int,
    ) -> MiniAppBridgePaymentEligibilityRead:
        """Track 5b.3b: read-only gate — client must then call existing Layer A payment-entry (no payment rows here)."""
        ctx = self._bridge.resolve_customer_execution_context(
            session,
            request_id=request_id,
            telegram_user_id=telegram_user_id,
        )
        effective = EffectiveCommercialExecutionPolicyService.resolve(
            tour=ctx.tour,
            request=ctx.request,
            response=ctx.response,
        )
        if not effective.platform_checkout_allowed:
            return MiniAppBridgePaymentEligibilityRead(
                payment_entry_allowed=False,
                order_id=None,
                effective_execution_policy=effective,
                blocked_code=effective.blocked_code or "platform_checkout_not_allowed",
                blocked_reason=effective.blocked_reason
                or "Platform checkout is not allowed for this RFQ context.",
            )

        order = session.get(Order, order_id)
        if order is None:
            return MiniAppBridgePaymentEligibilityRead(
                payment_entry_allowed=False,
                order_id=None,
                effective_execution_policy=effective,
                blocked_code="order_not_found",
                blocked_reason="Order not found.",
            )
        if order.user_id != ctx.user.id:
            return MiniAppBridgePaymentEligibilityRead(
                payment_entry_allowed=False,
                order_id=None,
                effective_execution_policy=effective,
                blocked_code="order_user_mismatch",
                blocked_reason="Order does not belong to this customer.",
            )
        if order.tour_id != ctx.tour.id:
            return MiniAppBridgePaymentEligibilityRead(
                payment_entry_allowed=False,
                order_id=None,
                effective_execution_policy=effective,
                blocked_code="order_bridge_tour_mismatch",
                blocked_reason="Order is not for the tour linked on this booking bridge.",
            )

        if not self._payment_entry.is_order_valid_for_payment_entry(
            session,
            order_id=order_id,
            user_id=ctx.user.id,
        ):
            return MiniAppBridgePaymentEligibilityRead(
                payment_entry_allowed=False,
                order_id=None,
                effective_execution_policy=effective,
                blocked_code="order_not_valid_for_payment",
                blocked_reason=(
                    "This order is not in a valid temporary reserved state for payment "
                    "(expired, wrong status, or already resolved)."
                ),
            )

        return MiniAppBridgePaymentEligibilityRead(
            payment_entry_allowed=True,
            order_id=order_id,
            effective_execution_policy=effective,
            blocked_code=None,
            blocked_reason=None,
        )


__all__ = [
    "BridgeExecutionBlocked",
    "BookingBridgeNotFoundError",
    "BookingBridgeValidationError",
    "CustomRequestBookingBridgeExecutionService",
]
