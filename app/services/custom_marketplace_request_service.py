"""Business rules for Layer C custom marketplace requests (Track 4–5a)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.custom_marketplace_request import CustomMarketplaceRequest, SupplierCustomRequestResponse
from app.models.enums import (
    CommercialResolutionKind,
    CustomMarketplaceRequestSource,
    CustomMarketplaceRequestStatus,
    SupplierCustomRequestResponseKind,
)
from app.models.supplier import Supplier
from app.repositories.custom_marketplace import (
    CustomMarketplaceRequestRepository,
    SupplierCustomRequestResponseRepository,
)
from app.repositories.user import UserRepository
from app.schemas.custom_marketplace import (
    AdminCustomRequestResolutionApply,
    BotCustomRequestCreate,
    CustomMarketplaceRequestDetailRead,
    CustomMarketplaceRequestRead,
    MiniAppCustomRequestCreate,
    MiniAppCustomRequestCustomerDetailRead,
    MiniAppCustomRequestCustomerListRead,
    MiniAppCustomRequestCustomerSummaryRead,
    SupplierCustomRequestResponseRead,
    SupplierCustomRequestResponseUpsert,
)
from app.services.custom_request_booking_bridge_service import CustomRequestBookingBridgeService


class CustomMarketplaceUserNotFoundError(Exception):
    pass


class CustomMarketplaceRequestNotFoundError(Exception):
    pass


class CustomMarketplaceRequestNotOpenError(Exception):
    def __init__(self, message: str = "Request is not open for supplier actions.") -> None:
        self.message = message
        super().__init__(message)


class CustomMarketplaceValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def customer_visible_summary(row: CustomMarketplaceRequest) -> str:
    """Minimal customer-facing copy (Track 5a) — not a quote comparison UI."""
    s = row.status
    if s == CustomMarketplaceRequestStatus.FULFILLED:
        return "This request was closed with team assistance."
    if s == CustomMarketplaceRequestStatus.OPEN:
        return "Your request is open. Suppliers may respond."
    if s == CustomMarketplaceRequestStatus.UNDER_REVIEW:
        return "Your request is under review."
    if s == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return "A supplier has been selected. Our team will contact you with next steps."
    if s == CustomMarketplaceRequestStatus.CLOSED_ASSISTED:
        return "This request was closed with team assistance."
    if s == CustomMarketplaceRequestStatus.CLOSED_EXTERNAL:
        return "This request was closed (recorded outside the automated checkout flow)."
    if s == CustomMarketplaceRequestStatus.CANCELLED:
        return "This request was cancelled."
    return "Your request status was updated."


class CustomMarketplaceRequestService:
    def __init__(self) -> None:
        self._requests = CustomMarketplaceRequestRepository()
        self._responses = SupplierCustomRequestResponseRepository()
        self._users = UserRepository()

    def create_from_mini_app(
        self,
        session: Session,
        *,
        payload: MiniAppCustomRequestCreate,
    ) -> CustomMarketplaceRequest:
        user = self._users.get_by_telegram_user_id(session, telegram_user_id=payload.telegram_user_id)
        if user is None:
            raise CustomMarketplaceUserNotFoundError
        travel_end = payload.travel_date_end or payload.travel_date_start
        row = CustomMarketplaceRequest(
            user_id=user.id,
            request_type=payload.request_type,
            travel_date_start=payload.travel_date_start,
            travel_date_end=travel_end if travel_end != payload.travel_date_start else payload.travel_date_end,
            route_notes=payload.route_notes.strip(),
            group_size=payload.group_size,
            special_conditions=payload.special_conditions,
            source_channel=CustomMarketplaceRequestSource.MINI_APP,
            status=CustomMarketplaceRequestStatus.OPEN,
        )
        if row.travel_date_end is not None and row.travel_date_end == row.travel_date_start:
            row.travel_date_end = None
        return self._requests.create(session, row=row)

    def create_from_bot(
        self,
        session: Session,
        *,
        payload: BotCustomRequestCreate,
    ) -> CustomMarketplaceRequest:
        user = self._users.get(session, payload.user_id)
        if user is None:
            raise CustomMarketplaceUserNotFoundError
        travel_end = payload.travel_date_end or payload.travel_date_start
        row = CustomMarketplaceRequest(
            user_id=user.id,
            request_type=payload.request_type,
            travel_date_start=payload.travel_date_start,
            travel_date_end=travel_end if travel_end != payload.travel_date_start else payload.travel_date_end,
            route_notes=payload.route_notes.strip(),
            group_size=payload.group_size,
            special_conditions=payload.special_conditions,
            source_channel=payload.source_channel,
            status=CustomMarketplaceRequestStatus.OPEN,
        )
        if row.travel_date_end is not None and row.travel_date_end == row.travel_date_start:
            row.travel_date_end = None
        return self._requests.create(session, row=row)

    def list_for_admin(
        self,
        session: Session,
        *,
        status: CustomMarketplaceRequestStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CustomMarketplaceRequestRead]:
        rows = self._requests.list_for_admin(session, status=status, limit=limit, offset=offset)
        return [CustomMarketplaceRequestRead.model_validate(r, from_attributes=True) for r in rows]

    def get_admin_detail(self, session: Session, *, request_id: int) -> CustomMarketplaceRequestDetailRead:
        row = self._requests.get_with_responses(session, request_id=request_id)
        if row is None:
            raise CustomMarketplaceRequestNotFoundError
        sel_id = row.selected_supplier_response_id
        responses = [_response_read(r, selected_supplier_response_id=sel_id) for r in row.supplier_responses]
        tg = row.user.telegram_user_id if row.user is not None else None
        bridge = CustomRequestBookingBridgeService().read_for_admin_detail(session, request_id=request_id)
        return CustomMarketplaceRequestDetailRead(
            request=CustomMarketplaceRequestRead.model_validate(row, from_attributes=True),
            responses=responses,
            customer_telegram_user_id=tg,
            booking_bridge=bridge,
        )

    def admin_patch(
        self,
        session: Session,
        *,
        request_id: int,
        admin_intervention_note: str | None,
        status: CustomMarketplaceRequestStatus | None,
    ) -> CustomMarketplaceRequestRead:
        row = self._requests.get(session, request_id=request_id)
        if row is None:
            raise CustomMarketplaceRequestNotFoundError
        if admin_intervention_note is not None:
            row.admin_intervention_note = admin_intervention_note
        if status is not None:
            if status == CustomMarketplaceRequestStatus.OPEN:
                row.selected_supplier_response_id = None
                row.commercial_resolution_kind = None
            if status == CustomMarketplaceRequestStatus.CANCELLED:
                row.selected_supplier_response_id = None
                row.commercial_resolution_kind = None
            row.status = status
        session.add(row)
        session.flush()
        session.refresh(row)
        return CustomMarketplaceRequestRead.model_validate(row, from_attributes=True)

    def admin_apply_resolution(
        self,
        session: Session,
        *,
        request_id: int,
        payload: AdminCustomRequestResolutionApply,
    ) -> CustomMarketplaceRequestRead:
        row = self._requests.get(session, request_id=request_id)
        if row is None:
            raise CustomMarketplaceRequestNotFoundError

        st = payload.status
        if st in (CustomMarketplaceRequestStatus.OPEN, CustomMarketplaceRequestStatus.CANCELLED):
            raise CustomMarketplaceValidationError("Use PATCH for open or cancelled statuses.")
        if st == CustomMarketplaceRequestStatus.FULFILLED:
            raise CustomMarketplaceValidationError(
                "Legacy fulfilled was migrated to closed_assisted; use a current resolution status.",
            )

        allowed = {
            CustomMarketplaceRequestStatus.UNDER_REVIEW,
            CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
            CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
        }
        if st not in allowed:
            raise CustomMarketplaceValidationError(f"Unsupported resolution status: {st}.")

        if payload.admin_intervention_note is not None:
            row.admin_intervention_note = payload.admin_intervention_note

        if st == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
            if payload.selected_supplier_response_id is None:
                raise CustomMarketplaceValidationError(
                    "selected_supplier_response_id is required when status is supplier_selected.",
                )
            resp = session.get(SupplierCustomRequestResponse, payload.selected_supplier_response_id)
            if resp is None or resp.request_id != request_id:
                raise CustomMarketplaceValidationError("Selected response does not belong to this request.")
            if resp.response_kind != SupplierCustomRequestResponseKind.PROPOSED:
                raise CustomMarketplaceValidationError("Only a proposed supplier response can be selected.")
            row.selected_supplier_response_id = payload.selected_supplier_response_id
            row.status = st
            if payload.commercial_resolution_kind is not None:
                row.commercial_resolution_kind = payload.commercial_resolution_kind
        elif st == CustomMarketplaceRequestStatus.CLOSED_ASSISTED:
            if payload.commercial_resolution_kind not in (
                None,
                CommercialResolutionKind.ASSISTED_CLOSURE,
            ):
                raise CustomMarketplaceValidationError(
                    "commercial_resolution_kind must be assisted_closure (or omitted) for closed_assisted.",
                )
            row.commercial_resolution_kind = CommercialResolutionKind.ASSISTED_CLOSURE
            row.status = st
        elif st == CustomMarketplaceRequestStatus.CLOSED_EXTERNAL:
            if payload.commercial_resolution_kind not in (
                None,
                CommercialResolutionKind.EXTERNAL_RECORD,
            ):
                raise CustomMarketplaceValidationError(
                    "commercial_resolution_kind must be external_record (or omitted) for closed_external.",
                )
            row.commercial_resolution_kind = CommercialResolutionKind.EXTERNAL_RECORD
            row.status = st
        elif st == CustomMarketplaceRequestStatus.UNDER_REVIEW:
            if payload.selected_supplier_response_id is not None:
                raise CustomMarketplaceValidationError(
                    "selected_supplier_response_id is not used when status is under_review.",
                )
            if payload.commercial_resolution_kind is not None:
                raise CustomMarketplaceValidationError(
                    "commercial_resolution_kind is not set when status is under_review.",
                )
            row.status = st

        session.add(row)
        session.flush()
        session.refresh(row)
        return CustomMarketplaceRequestRead.model_validate(row, from_attributes=True)

    def list_open_for_supplier(
        self,
        session: Session,
        *,
        supplier_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CustomMarketplaceRequestRead]:
        rows = self._requests.list_for_supplier_portal(
            session,
            supplier_id=supplier_id,
            limit=limit,
            offset=offset,
        )
        return [CustomMarketplaceRequestRead.model_validate(r, from_attributes=True) for r in rows]

    def get_open_for_supplier(
        self,
        session: Session,
        *,
        request_id: int,
        supplier_id: int,
    ) -> CustomMarketplaceRequestDetailRead:
        row = self._requests.get_for_supplier_view(
            session,
            request_id=request_id,
            supplier_id=supplier_id,
        )
        if row is None:
            raise CustomMarketplaceRequestNotFoundError
        existing = self._responses.get_for_supplier(session, request_id=request_id, supplier_id=supplier_id)
        sel_id = row.selected_supplier_response_id
        responses = (
            [_response_read(existing, selected_supplier_response_id=sel_id)]
            if existing is not None
            else []
        )
        tg = row.user.telegram_user_id if row.user is not None else None
        return CustomMarketplaceRequestDetailRead(
            request=CustomMarketplaceRequestRead.model_validate(row, from_attributes=True),
            responses=responses,
            customer_telegram_user_id=tg,
        )

    def upsert_supplier_response(
        self,
        session: Session,
        *,
        request_id: int,
        supplier_id: int,
        payload: SupplierCustomRequestResponseUpsert,
    ) -> SupplierCustomRequestResponseRead:
        req = self._requests.get(session, request_id=request_id)
        if req is None:
            raise CustomMarketplaceRequestNotFoundError
        if req.status not in (
            CustomMarketplaceRequestStatus.OPEN,
            CustomMarketplaceRequestStatus.UNDER_REVIEW,
        ):
            raise CustomMarketplaceRequestNotOpenError
        msg = payload.supplier_message
        if payload.response_kind == SupplierCustomRequestResponseKind.DECLINED:
            msg = (msg or "").strip() or None
        row = self._responses.upsert(
            session,
            request_id=request_id,
            supplier_id=supplier_id,
            response_kind=payload.response_kind,
            supplier_message=msg,
            quoted_price=payload.quoted_price,
            quoted_currency=payload.quoted_currency,
        )
        session.refresh(row)
        sup = session.get(Supplier, supplier_id)
        return _response_read(row, supplier=sup, selected_supplier_response_id=req.selected_supplier_response_id)

    def list_for_customer_mini_app(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> MiniAppCustomRequestCustomerListRead:
        user = self._users.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        if user is None:
            raise CustomMarketplaceUserNotFoundError
        rows = self._requests.list_for_customer_user(
            session,
            user_id=user.id,
            limit=limit,
            offset=offset,
        )
        items = [
            MiniAppCustomRequestCustomerSummaryRead(
                id=r.id,
                status=r.status,
                customer_visible_summary=customer_visible_summary(r),
            )
            for r in rows
        ]
        return MiniAppCustomRequestCustomerListRead(items=items, total_returned=len(items))

    def get_customer_detail_mini_app(
        self,
        session: Session,
        *,
        request_id: int,
        telegram_user_id: int,
    ) -> MiniAppCustomRequestCustomerDetailRead:
        user = self._users.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        if user is None:
            raise CustomMarketplaceUserNotFoundError
        row = self._requests.get_for_customer_user(session, request_id=request_id, user_id=user.id)
        if row is None:
            raise CustomMarketplaceRequestNotFoundError
        return MiniAppCustomRequestCustomerDetailRead(
            id=row.id,
            status=row.status,
            customer_visible_summary=customer_visible_summary(row),
            request_type=row.request_type,
            travel_date_start=row.travel_date_start,
            travel_date_end=row.travel_date_end,
        )


def _response_read(
    row: SupplierCustomRequestResponse,
    *,
    supplier: Supplier | None = None,
    selected_supplier_response_id: int | None = None,
) -> SupplierCustomRequestResponseRead:
    code = None
    name = None
    sup = supplier if supplier is not None else getattr(row, "supplier", None)
    if sup is not None:
        code = sup.code
        name = sup.display_name
    is_selected = (
        selected_supplier_response_id is not None and row.id == selected_supplier_response_id
    )
    return SupplierCustomRequestResponseRead(
        id=row.id,
        request_id=row.request_id,
        supplier_id=row.supplier_id,
        supplier_code=code,
        supplier_display_name=name,
        response_kind=row.response_kind,
        supplier_message=row.supplier_message,
        quoted_price=row.quoted_price,
        quoted_currency=row.quoted_currency,
        is_selected=is_selected,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
