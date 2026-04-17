"""Track 5b.2: explicit RFQ bridge → Layer A preparation + temporary reservation (orchestration only)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import CustomRequestBookingBridgeStatus
from app.schemas.mini_app import MiniAppBridgeExecutionPreparationResponse
from app.schemas.prepared import OrderSummaryRead
from app.services.custom_request_booking_bridge_service import (
    BookingBridgeNotFoundError,
    BookingBridgeValidationError,
    CustomRequestBookingBridgeService,
)
from app.services.mini_app_booking import MiniAppBookingService, MiniAppSelfServiceBookingNotAllowedError
from app.services.mini_app_reservation_preparation import MiniAppReservationPreparationService
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


class CustomRequestBookingBridgeExecutionService:
    def __init__(
        self,
        *,
        bridge_service: CustomRequestBookingBridgeService | None = None,
        preparation_service: MiniAppReservationPreparationService | None = None,
        booking_service: MiniAppBookingService | None = None,
    ) -> None:
        self._bridge = bridge_service or CustomRequestBookingBridgeService()
        self._preparation = preparation_service or MiniAppReservationPreparationService()
        self._booking = booking_service or MiniAppBookingService()

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
        if not policy.per_seat_self_service_allowed:
            return MiniAppBridgeExecutionPreparationResponse(
                self_service_available=False,
                blocked_code="operator_assistance_required",
                blocked_message=_MSG_OPERATOR_ASSISTANCE,
                preparation=None,
                tour_code=ctx.tour.code,
                sales_mode_policy=policy,
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
            )

        return MiniAppBridgeExecutionPreparationResponse(
            self_service_available=True,
            blocked_code=None,
            blocked_message=None,
            preparation=prep,
            tour_code=ctx.tour.code,
            sales_mode_policy=policy,
        )

    def create_execution_reservation(
        self,
        session: Session,
        *,
        request_id: int,
        telegram_user_id: int,
        seats_count: int,
        boarding_point_id: int,
        language_code: str | None = None,
    ) -> OrderSummaryRead:
        """Re-validates bridge context, enforces sales-mode policy, then existing Mini App hold path."""
        ctx = self._bridge.resolve_customer_execution_context(
            session,
            request_id=request_id,
            telegram_user_id=telegram_user_id,
        )
        policy = TourSalesModePolicyService.policy_for_tour(ctx.tour)
        if not policy.per_seat_self_service_allowed:
            raise BridgeExecutionBlocked(
                code="operator_assistance_required",
                message=_MSG_OPERATOR_ASSISTANCE,
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


__all__ = [
    "BridgeExecutionBlocked",
    "BookingBridgeNotFoundError",
    "BookingBridgeValidationError",
    "CustomRequestBookingBridgeExecutionService",
]
