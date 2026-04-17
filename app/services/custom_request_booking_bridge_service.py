"""Track 5b.1: admin-triggered RFQ booking bridge — no reservation or payment.

Track 5b.2 adds customer execution context resolution (orchestration only — Layer A holds unchanged).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.custom_marketplace_request import CustomMarketplaceRequest, SupplierCustomRequestResponse
from app.models.custom_request_booking_bridge import CustomRequestBookingBridge
from app.models.enums import (
    CustomMarketplaceRequestStatus,
    CustomRequestBookingBridgeStatus,
    SupplierCustomRequestResponseKind,
    TourStatus,
)
from app.models.tour import Tour
from app.models.user import User
from app.repositories.custom_request_booking_bridge import CustomRequestBookingBridgeRepository
from app.repositories.user import UserRepository
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.schemas.custom_marketplace import (
    AdminCustomRequestBookingBridgeCreate,
    AdminCustomRequestBookingBridgePatch,
    CustomRequestBookingBridgeRead,
)


class BookingBridgeError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class BookingBridgeValidationError(BookingBridgeError):
    pass


class BookingBridgeConflictError(BookingBridgeError):
    pass


class BookingBridgeNotFoundError(BookingBridgeError):
    pass


@dataclass(frozen=True)
class CustomerBridgeExecutionContext:
    """Validated RFQ bridge + request + tour + customer for explicit Layer A entry (Track 5b.2)."""

    bridge: CustomRequestBookingBridge
    request: CustomMarketplaceRequest
    response: SupplierCustomRequestResponse
    tour: Tour
    user: User


_ALLOWED_REQUEST_STATUSES: frozenset[CustomMarketplaceRequestStatus] = frozenset(
    {
        CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
    },
)


class CustomRequestBookingBridgeService:
    def __init__(self) -> None:
        self._bridges = CustomRequestBookingBridgeRepository()

    def to_read(self, row: CustomRequestBookingBridge) -> CustomRequestBookingBridgeRead:
        return CustomRequestBookingBridgeRead.model_validate(row, from_attributes=True)

    def _validate_tour_for_future_execution(self, session: Session, *, tour_id: int) -> Tour:
        tour = session.get(Tour, tour_id)
        if tour is None:
            raise BookingBridgeValidationError("Tour not found.")
        if tour.status != TourStatus.OPEN_FOR_SALE:
            raise BookingBridgeValidationError("Tour must be open_for_sale to link on a booking bridge.")
        now = datetime.now(UTC)
        if tour.departure_datetime <= now:
            raise BookingBridgeValidationError("Tour departure must be in the future.")
        if tour.sales_deadline is not None and tour.sales_deadline <= now:
            raise BookingBridgeValidationError("Tour sales_deadline must be in the future (or null).")
        if tour.seats_available < 1:
            raise BookingBridgeValidationError("Tour must have at least one available seat for future booking.")
        return tour

    def load_tour_validated_for_customer_execution(self, session: Session, *, tour_id: int) -> Tour:
        """Same window checks as bridge link time, plus customer-facing catalog visibility (time only)."""
        tour = self._validate_tour_for_future_execution(session, tour_id=tour_id)
        if not tour_is_customer_catalog_visible(
            departure_datetime=tour.departure_datetime,
            sales_deadline=tour.sales_deadline,
        ):
            raise BookingBridgeValidationError(
                "Tour is not in a customer-bookable window (departure or sales deadline).",
            )
        return tour

    def resolve_customer_execution_context(
        self,
        session: Session,
        *,
        request_id: int,
        telegram_user_id: int,
    ) -> CustomerBridgeExecutionContext:
        """Explicit execution gate: active bridge, linked tour, request/selection integrity, owning user."""
        user = UserRepository().get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        if user is None:
            raise BookingBridgeNotFoundError("User not found.")
        req = session.get(CustomMarketplaceRequest, request_id)
        if req is None:
            raise BookingBridgeNotFoundError("Request not found.")
        if req.user_id != user.id:
            raise BookingBridgeValidationError("Request does not belong to this user.")
        bridge = self._bridges.get_active_for_request(session, request_id=request_id)
        if bridge is None:
            raise BookingBridgeNotFoundError("No active booking bridge for this request.")
        if bridge.user_id != user.id:
            raise BookingBridgeValidationError("Booking bridge does not match this user.")
        if bridge.tour_id is None:
            raise BookingBridgeValidationError(
                "Booking bridge has no linked tour. Ask the team to link a tour before continuing.",
            )
        resp = self._validate_eligibility(session, req=req)
        if (
            bridge.selected_supplier_response_id != resp.id
            or req.selected_supplier_response_id != resp.id
        ):
            raise BookingBridgeValidationError(
                "Booking bridge is out of sync with the current request selection.",
            )
        tour = self.load_tour_validated_for_customer_execution(session, tour_id=bridge.tour_id)
        return CustomerBridgeExecutionContext(
            bridge=bridge,
            request=req,
            response=resp,
            tour=tour,
            user=user,
        )

    def _validate_eligibility(
        self,
        session: Session,
        *,
        req: CustomMarketplaceRequest,
    ) -> SupplierCustomRequestResponse:
        if req.status not in _ALLOWED_REQUEST_STATUSES:
            raise BookingBridgeValidationError(
                "Request status must be supplier_selected or closed_assisted to create a booking bridge.",
            )
        if req.selected_supplier_response_id is None:
            raise BookingBridgeValidationError("Request has no selected supplier response.")
        resp = session.get(SupplierCustomRequestResponse, req.selected_supplier_response_id)
        if resp is None:
            raise BookingBridgeValidationError("Selected supplier response not found.")
        if resp.request_id != req.id:
            raise BookingBridgeValidationError("Selected response does not belong to this request.")
        if resp.response_kind != SupplierCustomRequestResponseKind.PROPOSED:
            raise BookingBridgeValidationError("Selected response must be proposed for a booking bridge.")
        return resp

    def create_bridge(
        self,
        session: Session,
        *,
        request_id: int,
        payload: AdminCustomRequestBookingBridgeCreate,
    ) -> CustomRequestBookingBridgeRead:
        req = session.get(CustomMarketplaceRequest, request_id)
        if req is None:
            raise BookingBridgeNotFoundError("Request not found.")

        if self._bridges.get_active_for_request(session, request_id=request_id) is not None:
            raise BookingBridgeConflictError("An active booking bridge already exists for this request.")

        resp = self._validate_eligibility(session, req=req)

        tour_id = payload.tour_id
        if tour_id is not None:
            self._validate_tour_for_future_execution(session, tour_id=tour_id)
            initial_status = CustomRequestBookingBridgeStatus.LINKED_TOUR
        else:
            initial_status = CustomRequestBookingBridgeStatus.READY

        row = CustomRequestBookingBridge(
            request_id=req.id,
            selected_supplier_response_id=resp.id,
            user_id=req.user_id,
            tour_id=tour_id,
            bridge_status=initial_status,
            admin_note=payload.admin_note,
        )
        self._bridges.create(session, row=row)
        return self.to_read(row)

    def patch_bridge(
        self,
        session: Session,
        *,
        request_id: int,
        payload: AdminCustomRequestBookingBridgePatch,
    ) -> CustomRequestBookingBridgeRead:
        active = self._bridges.get_active_for_request(session, request_id=request_id)
        if active is None:
            raise BookingBridgeNotFoundError("No active booking bridge for this request.")

        if payload.admin_note is not None:
            active.admin_note = payload.admin_note

        if payload.tour_id is not None:
            self._validate_tour_for_future_execution(session, tour_id=payload.tour_id)
            active.tour_id = payload.tour_id
            if active.bridge_status in (
                CustomRequestBookingBridgeStatus.READY,
                CustomRequestBookingBridgeStatus.PENDING_VALIDATION,
            ):
                active.bridge_status = CustomRequestBookingBridgeStatus.LINKED_TOUR

        session.add(active)
        session.flush()
        session.refresh(active)
        return self.to_read(active)

    def read_for_admin_detail(
        self,
        session: Session,
        *,
        request_id: int,
    ) -> CustomRequestBookingBridgeRead | None:
        row = self._bridges.get_latest_for_request(session, request_id=request_id)
        if row is None:
            return None
        return self.to_read(row)
