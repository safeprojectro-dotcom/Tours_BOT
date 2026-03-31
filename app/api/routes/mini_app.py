from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.mini_app import (
    MiniAppBookingDetailRead,
    MiniAppBookingsListRead,
    MiniAppCatalogFiltersRead,
    MiniAppCatalogRead,
    MiniAppCreateReservationRequest,
    MiniAppPaymentEntryRequest,
    MiniAppReservationPreparationRead,
    MiniAppTourDetailRead,
)
from app.schemas.prepared import OrderSummaryRead, PaymentEntryRead, ReservationPreparationSummaryRead
from app.services.catalog import CatalogLookupService
from app.services.mini_app_booking import MiniAppBookingService
from app.services.mini_app_bookings import MiniAppBookingsService
from app.services.mini_app_catalog import MiniAppCatalogService
from app.services.mini_app_reservation_preparation import MiniAppReservationPreparationService
from app.services.mini_app_tour_detail import MiniAppTourDetailService

router = APIRouter(prefix="/mini-app", tags=["mini-app"])


@router.get("/bookings", response_model=MiniAppBookingsListRead)
def list_my_bookings(
    telegram_user_id: int = Query(gt=0),
    language_code: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
) -> MiniAppBookingsListRead:
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
    summary = MiniAppBookingService().create_temporary_reservation(
        session,
        tour_code=tour_code,
        telegram_user_id=payload.telegram_user_id,
        seats_count=payload.seats_count,
        boarding_point_id=payload.boarding_point_id,
        language_code=language_code,
    )
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
