from __future__ import annotations

import json
import time
from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.custom_marketplace import (
    MiniAppCustomRequestCreate,
    MiniAppCustomRequestCreatedRead,
    MiniAppCustomRequestCustomerDetailRead,
    MiniAppCustomRequestCustomerListRead,
)
from app.schemas.mini_app import (
    MiniAppBookingDetailRead,
    MiniAppBookingsListRead,
    MiniAppBridgeExecutionPreparationResponse,
    MiniAppBridgePaymentEligibilityRead,
    MiniAppCatalogFiltersRead,
    MiniAppCatalogRead,
    MiniAppCreateReservationRequest,
    MiniAppHelpRead,
    MiniAppLanguagePreferenceRequest,
    MiniAppLanguagePreferenceResponse,
    MiniAppPaymentEntryRequest,
    MiniAppReservationPreparationRead,
    MiniAppSettingsRead,
    MiniAppSupplierOfferLandingRead,
    MiniAppSupportRequest,
    MiniAppSupportRequestResponse,
    MiniAppTourDetailRead,
    MiniAppWaitlistJoinRequest,
    MiniAppWaitlistJoinResponse,
    MiniAppWaitlistStatusRead,
)
from app.schemas.payment import PaymentReconciliationRead
from app.schemas.prepared import OrderSummaryRead, PaymentEntryRead, ReservationPreparationSummaryRead
from app.services.catalog import CatalogLookupService
from app.services.mini_app_booking import (
    MiniAppBookingService,
    MiniAppCharterSeatsCountMismatchError,
    MiniAppSelfServiceBookingNotAllowedError,
)
from app.services.mini_app_bookings import MiniAppBookingsService
from app.services.mini_app_catalog import MiniAppCatalogService
from app.repositories.tour import TourRepository
from app.services.handoff_entry import HandoffEntryService
from app.services.mini_app_help_settings import MiniAppHelpSettingsService
from app.services.mini_app_reservation_preparation import MiniAppReservationPreparationService
from app.services.mini_app_mock_payment import MiniAppMockPaymentCompletionService
from app.services.mini_app_supplier_offer_landing import MiniAppSupplierOfferLandingService
from app.services.mini_app_tour_detail import MiniAppTourDetailService
from app.services.mini_app_waitlist import MiniAppWaitlistService
from app.services.tour_sales_mode_policy import TourSalesModePolicyService
from app.services.custom_marketplace_request_service import (
    CustomMarketplaceRequestNotFoundError,
    CustomMarketplaceRequestService,
    CustomMarketplaceUserNotFoundError,
)
from app.services.custom_request_booking_bridge_execution import (
    BridgeExecutionBlocked,
    CustomRequestBookingBridgeExecutionService,
)
from app.services.custom_request_booking_bridge_service import (
    BookingBridgeNotFoundError,
    BookingBridgeValidationError,
)

router = APIRouter(prefix="/mini-app", tags=["mini-app"])
DEBUG_LOG_PATH = Path("debug-7dffdf.log")


def _agent_debug_log(
    *,
    run_id: str,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, object],
) -> None:
    payload = {
        "sessionId": "7dffdf",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        return


@router.get("/bookings", response_model=MiniAppBookingsListRead)
def list_my_bookings(
    telegram_user_id: int = Query(gt=0),
    language_code: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
) -> MiniAppBookingsListRead:
    # region agent log
    _agent_debug_log(
        run_id="baseline",
        hypothesis_id="H5",
        location="app/api/routes/mini_app.py:list_my_bookings",
        message="backend received bookings identity query",
        data={"telegram_user_id_present": telegram_user_id > 0},
    )
    # endregion
    return MiniAppBookingsService().list_bookings(
        session,
        telegram_user_id=telegram_user_id,
        language_code=language_code,
        limit=limit,
        offset=offset,
    )


@router.get("/orders/{order_id}/booking-status", response_model=MiniAppBookingDetailRead)
def get_booking_status(
    order_id: int,
    telegram_user_id: int = Query(gt=0),
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> MiniAppBookingDetailRead:
    detail = MiniAppBookingsService().get_booking_detail(
        session,
        order_id=order_id,
        telegram_user_id=telegram_user_id,
        language_code=language_code,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="booking not found")
    return detail


@router.get("/help", response_model=MiniAppHelpRead)
def get_mini_app_help(
    language_code: str | None = Query(default=None, max_length=16),
) -> MiniAppHelpRead:
    return MiniAppHelpSettingsService().get_help_read(language_code=language_code)


@router.post("/custom-requests", response_model=MiniAppCustomRequestCreatedRead, status_code=status.HTTP_201_CREATED)
def post_mini_app_custom_request(
    payload: MiniAppCustomRequestCreate,
    session: Session = Depends(get_db),
) -> MiniAppCustomRequestCreatedRead:
    """Structured RFQ intake (Layer C). Does not create an order or reservation."""
    try:
        row = CustomMarketplaceRequestService().create_from_mini_app(session, payload=payload)
    except CustomMarketplaceUserNotFoundError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown telegram_user_id — open the bot once or complete a catalog action first.",
        ) from None
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    session.commit()
    return MiniAppCustomRequestCreatedRead(id=row.id, status=row.status)


@router.get("/custom-requests", response_model=MiniAppCustomRequestCustomerListRead)
def list_mini_app_custom_requests_for_customer(
    telegram_user_id: int = Query(gt=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
) -> MiniAppCustomRequestCustomerListRead:
    """Minimal RFQ status for the requester (Track 5a) — no supplier quote comparison."""
    # region agent log
    _agent_debug_log(
        run_id="baseline",
        hypothesis_id="H5",
        location="app/api/routes/mini_app.py:list_mini_app_custom_requests_for_customer",
        message="backend received my-requests list identity query",
        data={"telegram_user_id_present": telegram_user_id > 0},
    )
    # endregion
    try:
        return CustomMarketplaceRequestService().list_for_customer_mini_app(
            session,
            telegram_user_id=telegram_user_id,
            limit=limit,
            offset=offset,
        )
    except CustomMarketplaceUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown telegram_user_id — open the bot once or complete a catalog action first.",
        ) from None


@router.get("/custom-requests/{request_id}", response_model=MiniAppCustomRequestCustomerDetailRead)
def get_mini_app_custom_request_for_customer(
    request_id: int,
    telegram_user_id: int = Query(gt=0),
    session: Session = Depends(get_db),
) -> MiniAppCustomRequestCustomerDetailRead:
    # region agent log
    _agent_debug_log(
        run_id="baseline",
        hypothesis_id="H5",
        location="app/api/routes/mini_app.py:get_mini_app_custom_request_for_customer",
        message="backend received my-request detail identity query",
        data={"telegram_user_id_present": telegram_user_id > 0, "request_id": request_id},
    )
    # endregion
    try:
        return CustomMarketplaceRequestService().get_customer_detail_mini_app(
            session,
            request_id=request_id,
            telegram_user_id=telegram_user_id,
        )
    except CustomMarketplaceUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown telegram_user_id — open the bot once or complete a catalog action first.",
        ) from None
    except CustomMarketplaceRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.") from None


@router.get(
    "/custom-requests/{request_id}/booking-bridge/preparation",
    response_model=MiniAppBridgeExecutionPreparationResponse,
)
def get_custom_request_booking_bridge_preparation(
    request_id: int,
    telegram_user_id: int = Query(gt=0),
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> MiniAppBridgeExecutionPreparationResponse:
    """Track 5b.2: explicit bridge execution entry — reuse Layer A preparation (no hold, no payment)."""
    try:
        return CustomRequestBookingBridgeExecutionService().get_execution_preparation(
            session,
            request_id=request_id,
            telegram_user_id=telegram_user_id,
            language_code=language_code,
        )
    except BookingBridgeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None
    except BookingBridgeValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from None


@router.post(
    "/custom-requests/{request_id}/booking-bridge/reservations",
    response_model=OrderSummaryRead,
)
def create_custom_request_booking_bridge_reservation(
    request_id: int,
    payload: MiniAppCreateReservationRequest,
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> OrderSummaryRead:
    """Track 5b.2: explicit bridge execution — reuse existing temporary reservation path (no new payment)."""
    try:
        summary = CustomRequestBookingBridgeExecutionService().create_execution_reservation(
            session,
            request_id=request_id,
            telegram_user_id=payload.telegram_user_id,
            seats_count=payload.seats_count,
            boarding_point_id=payload.boarding_point_id,
            language_code=language_code,
        )
    except BookingBridgeNotFoundError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None
    except BookingBridgeValidationError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from None
    except BridgeExecutionBlocked as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message},
        ) from None
    session.commit()
    return summary


@router.get(
    "/custom-requests/{request_id}/booking-bridge/payment-eligibility",
    response_model=MiniAppBridgePaymentEligibilityRead,
)
def get_custom_request_booking_bridge_payment_eligibility(
    request_id: int,
    telegram_user_id: int = Query(gt=0),
    order_id: int = Query(gt=0),
    session: Session = Depends(get_db),
) -> MiniAppBridgePaymentEligibilityRead:
    """Track 5b.3b: read-only payment gate — reuse ``POST /mini-app/orders/{order_id}/payment-entry`` when allowed."""
    try:
        return CustomRequestBookingBridgeExecutionService().get_payment_eligibility(
            session,
            request_id=request_id,
            telegram_user_id=telegram_user_id,
            order_id=order_id,
        )
    except BookingBridgeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None
    except BookingBridgeValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from None


@router.post("/support-request", response_model=MiniAppSupportRequestResponse)
def post_mini_app_support_request(
    payload: MiniAppSupportRequest,
    session: Session = Depends(get_db),
) -> MiniAppSupportRequestResponse:
    service = HandoffEntryService()
    hint = (payload.screen_hint or "unknown").replace("|", " ").strip()[:40] or "unknown"
    reason = f"{HandoffEntryService.REASON_MINI_APP_PREFIX}|{hint}"[:255]
    tour_code = (payload.tour_code or "").strip()
    if tour_code:
        tour = TourRepository().get_by_code(session, code=tour_code)
        if tour is not None and not TourSalesModePolicyService.policy_for_sales_mode(
            tour.sales_mode
        ).per_seat_self_service_allowed:
            reason = HandoffEntryService.build_full_bus_sales_assistance_reason(
                tour_code=tour.code,
                sales_mode=tour.sales_mode.value,
                channel="mini_app",
                screen_hint=payload.screen_hint,
            )
    handoff_id = service.create_for_telegram_user(
        session,
        telegram_user_id=payload.telegram_user_id,
        reason=reason,
        order_id=payload.order_id,
    )
    if handoff_id is None:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="support request could not be recorded",
        )
    session.commit()
    return MiniAppSupportRequestResponse(recorded=True, handoff_id=handoff_id)


@router.get("/settings", response_model=MiniAppSettingsRead)
def get_mini_app_ui_settings(
    telegram_user_id: int | None = Query(default=None),
    session: Session = Depends(get_db),
) -> MiniAppSettingsRead:
    tid = telegram_user_id if telegram_user_id is not None and telegram_user_id > 0 else None
    # region agent log
    _agent_debug_log(
        run_id="baseline",
        hypothesis_id="H5",
        location="app/api/routes/mini_app.py:get_mini_app_ui_settings",
        message="backend received settings identity query",
        data={"telegram_user_id_present": tid is not None},
    )
    # endregion
    return MiniAppHelpSettingsService().get_settings_read(session, telegram_user_id=tid)


@router.get("/supplier-offers/{supplier_offer_id}", response_model=MiniAppSupplierOfferLandingRead)
def get_supplier_offer_landing(
    supplier_offer_id: int,
    session: Session = Depends(get_db),
) -> MiniAppSupplierOfferLandingRead:
    detail = MiniAppSupplierOfferLandingService().get_published_offer_landing(
        session,
        supplier_offer_id=supplier_offer_id,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="supplier offer not found")
    return detail


@router.post("/language-preference", response_model=MiniAppLanguagePreferenceResponse)
def post_mini_app_language_preference(
    payload: MiniAppLanguagePreferenceRequest,
    session: Session = Depends(get_db),
) -> MiniAppLanguagePreferenceResponse:
    # region agent log
    _agent_debug_log(
        run_id="baseline",
        hypothesis_id="H5",
        location="app/api/routes/mini_app.py:post_mini_app_language_preference",
        message="backend received settings save identity body",
        data={"telegram_user_id_present": payload.telegram_user_id > 0},
    )
    # endregion
    service = MiniAppHelpSettingsService()
    applied = service.set_language_preference(
        session,
        telegram_user_id=payload.telegram_user_id,
        language_code=payload.language_code,
    )
    if applied is None:
        session.rollback()
        raise HTTPException(status_code=400, detail="unsupported language code")
    session.commit()
    return MiniAppLanguagePreferenceResponse(language_code=applied)


@router.get("/catalog", response_model=MiniAppCatalogRead)
def get_catalog(
    language_code: str | None = Query(default=None),
    destination_query: str | None = Query(default=None, max_length=200),
    departure_date_from: date | None = Query(default=None),
    departure_date_to: date | None = Query(default=None),
    max_price: Decimal | None = Query(default=None, ge=0),
    limit: int = Query(default=MiniAppCatalogService.DEFAULT_LIMIT, ge=1, le=MiniAppCatalogService.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
) -> MiniAppCatalogRead:
    service = MiniAppCatalogService()
    filters = MiniAppCatalogFiltersRead(
        departure_date_from=departure_date_from,
        departure_date_to=departure_date_to,
        destination_query=destination_query,
        max_price=max_price,
    )
    try:
        return service.list_catalog(
            session,
            language_code=language_code,
            filters=filters,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tours/{tour_code}", response_model=MiniAppTourDetailRead)
def get_tour_detail(
    tour_code: str,
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> MiniAppTourDetailRead:
    detail = MiniAppTourDetailService().get_tour_detail(
        session,
        code=tour_code,
        language_code=language_code,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="tour not found")
    return detail


@router.get("/tours/{tour_code}/waitlist-status", response_model=MiniAppWaitlistStatusRead)
def get_waitlist_status(
    tour_code: str,
    telegram_user_id: int = Query(gt=0),
    session: Session = Depends(get_db),
) -> MiniAppWaitlistStatusRead:
    eligible, on_waitlist, waitlist_status, entry_id = MiniAppWaitlistService().get_status(
        session,
        tour_code=tour_code,
        telegram_user_id=telegram_user_id,
    )
    return MiniAppWaitlistStatusRead(
        eligible=eligible,
        on_waitlist=on_waitlist,
        waitlist_status=waitlist_status,
        waitlist_entry_id=entry_id,
    )


@router.post("/tours/{tour_code}/waitlist", response_model=MiniAppWaitlistJoinResponse)
def join_waitlist(
    tour_code: str,
    payload: MiniAppWaitlistJoinRequest,
    session: Session = Depends(get_db),
) -> MiniAppWaitlistJoinResponse:
    outcome, entry_id = MiniAppWaitlistService().join(
        session,
        tour_code=tour_code,
        telegram_user_id=payload.telegram_user_id,
        seats_count=payload.seats_count,
    )
    session.commit()
    return MiniAppWaitlistJoinResponse(outcome=outcome.value, waitlist_entry_id=entry_id)


@router.get("/tours/{tour_code}/preparation", response_model=MiniAppReservationPreparationRead)
def get_tour_preparation(
    tour_code: str,
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> MiniAppReservationPreparationRead:
    preparation = MiniAppReservationPreparationService().get_preparation(
        session,
        code=tour_code,
        language_code=language_code,
    )
    if preparation is None:
        raise HTTPException(status_code=404, detail="tour is not available for reservation preparation")
    return preparation


@router.get(
    "/tours/{tour_code}/preparation-summary",
    response_model=ReservationPreparationSummaryRead,
)
def get_tour_preparation_summary(
    tour_code: str,
    seats_count: int = Query(ge=1),
    boarding_point_id: int = Query(ge=1),
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> ReservationPreparationSummaryRead:
    summary = MiniAppReservationPreparationService().build_preparation_summary(
        session,
        code=tour_code,
        seats_count=seats_count,
        boarding_point_id=boarding_point_id,
        language_code=language_code,
    )
    if summary is None:
        raise HTTPException(status_code=400, detail="invalid reservation preparation selection")
    return summary


@router.post(
    "/tours/{tour_code}/reservations",
    response_model=OrderSummaryRead,
)
def create_temporary_reservation(
    tour_code: str,
    payload: MiniAppCreateReservationRequest,
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> OrderSummaryRead:
    try:
        summary = MiniAppBookingService().create_temporary_reservation(
            session,
            tour_code=tour_code,
            telegram_user_id=payload.telegram_user_id,
            seats_count=payload.seats_count,
            boarding_point_id=payload.boarding_point_id,
            language_code=language_code,
        )
    except MiniAppSelfServiceBookingNotAllowedError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail={
                "code": MiniAppSelfServiceBookingNotAllowedError.code,
                "message": "Self-service reservation is not available for this tour sales mode.",
            },
        ) from None
    except MiniAppCharterSeatsCountMismatchError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail={
                "code": MiniAppCharterSeatsCountMismatchError.code,
                "message": "Whole-bus catalog reservation must use the full configured seat count.",
            },
        ) from None
    if summary is None:
        session.rollback()
        if CatalogLookupService().get_tour_by_code(session, code=tour_code) is None:
            raise HTTPException(status_code=404, detail="tour not found")
        raise HTTPException(
            status_code=400,
            detail="temporary reservation could not be created",
        )
    session.commit()
    return summary


@router.get(
    "/orders/{order_id}/reservation-overview",
    response_model=OrderSummaryRead,
)
def get_reservation_overview(
    order_id: int,
    telegram_user_id: int = Query(gt=0),
    language_code: str | None = Query(default=None),
    session: Session = Depends(get_db),
) -> OrderSummaryRead:
    summary = MiniAppBookingService().get_reservation_overview_for_user(
        session,
        order_id=order_id,
        telegram_user_id=telegram_user_id,
        language_code=language_code,
    )
    if summary is None:
        raise HTTPException(status_code=404, detail="reservation overview not found")
    return summary


@router.post(
    "/orders/{order_id}/payment-entry",
    response_model=PaymentEntryRead,
)
def start_payment_entry(
    order_id: int,
    payload: MiniAppPaymentEntryRequest,
    session: Session = Depends(get_db),
) -> PaymentEntryRead:
    entry = MiniAppBookingService().start_payment_entry(
        session,
        order_id=order_id,
        telegram_user_id=payload.telegram_user_id,
    )
    if entry is None:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="payment entry is not available for this order",
        )
    session.commit()
    return entry


@router.post(
    "/orders/{order_id}/mock-payment-complete",
    response_model=PaymentReconciliationRead,
)
def complete_mock_payment(
    order_id: int,
    payload: MiniAppPaymentEntryRequest,
    session: Session = Depends(get_db),
) -> PaymentReconciliationRead:
    if not get_settings().enable_mock_payment_completion:
        raise HTTPException(status_code=403, detail="mock payment completion is disabled")
    result = MiniAppMockPaymentCompletionService().complete_mock_payment_for_order(
        session,
        order_id=order_id,
        telegram_user_id=payload.telegram_user_id,
    )
    if result is None:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="mock payment could not be completed for this order",
        )
    session.commit()
    return result
