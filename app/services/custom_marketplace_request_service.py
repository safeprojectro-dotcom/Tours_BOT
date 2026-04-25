"""Business rules for Layer C custom marketplace requests (Track 4–5a)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.custom_marketplace_request import CustomMarketplaceRequest, SupplierCustomRequestResponse
from app.models.enums import (
    CommercialResolutionKind,
    CustomerCommercialMode,
    CustomMarketplaceRequestSource,
    CustomMarketplaceRequestStatus,
    SupplierCustomRequestResponseKind,
    SupplierOfferPaymentMode,
    TourSalesMode,
)
from app.models.supplier import Supplier
from app.repositories.custom_marketplace import (
    CustomMarketplaceRequestRepository,
    SupplierCustomRequestResponseRepository,
)
from app.repositories.custom_request_booking_bridge import CustomRequestBookingBridgeRepository
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
    MiniAppSelectedOfferSummaryRead,
    SupplierCustomRequestResponseRead,
    SupplierCustomRequestResponseUpsert,
)
from app.models.tour import Tour
from app.services.admin_customer_summary import build_admin_customer_summary_from_user
from app.services.custom_request_booking_bridge_service import CustomRequestBookingBridgeService
from app.services.custom_request_lifecycle_preview import CustomRequestLifecyclePreviewService
from app.services.effective_commercial_execution_policy import EffectiveCommercialExecutionPolicyService
from app.services.operational_custom_request_hints import (
    build_operational_detail_hints,
    build_operational_list_hints,
)
from app.services.supplier_custom_request_portal_hints import build_supplier_portal_hints


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


_CUSTOMER_OFFER_MESSAGE_EXCERPT_MAX = 200
_CUSTOMER_ROUTE_NOTES_PREVIEW_MAX = 96


def _single_line_text(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    return " ".join(text.split())


def _customer_route_notes_preview(row: CustomMarketplaceRequest) -> str | None:
    compact = _single_line_text(row.route_notes)
    if not compact:
        return None
    if len(compact) <= _CUSTOMER_ROUTE_NOTES_PREVIEW_MAX:
        return compact
    return f"{compact[:_CUSTOMER_ROUTE_NOTES_PREVIEW_MAX - 1].rstrip()}…"


def _customer_offers_received_hint(
    *,
    status: CustomMarketplaceRequestStatus,
    proposed_count: int,
    language_code: str | None = None,
) -> str:
    """Track 5f v1: neutral copy for Mini App; U3 adds Romanian when preferred language is ro."""
    code = (language_code or "en").lower().split("-")[0]
    if code == "ro":
        return _customer_offers_received_hint_ro(status=status, proposed_count=proposed_count)
    if status in (
        CustomMarketplaceRequestStatus.OPEN,
        CustomMarketplaceRequestStatus.UNDER_REVIEW,
    ):
        if proposed_count == 0:
            return "No supplier proposals are on file yet for this request."
        if proposed_count == 1:
            return "One supplier proposal has been received and may be under review."
        return (
            f"{proposed_count} supplier proposals have been received and may be under review."
        )
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return (
            "The team has selected a supplier proposal. Next steps depend on your case and "
            "any booking link from the team."
        )
    if status in (
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
        CustomMarketplaceRequestStatus.FULFILLED,
    ):
        return "This request was handled with team assistance."
    if status == CustomMarketplaceRequestStatus.CLOSED_EXTERNAL:
        return "This request was closed outside the in-app checkout flow."
    if status == CustomMarketplaceRequestStatus.CANCELLED:
        return ""
    return ""


def _customer_offers_received_hint_ro(
    *,
    status: CustomMarketplaceRequestStatus,
    proposed_count: int,
) -> str:
    """Romanian mirror of _customer_offers_received_hint (presentation only)."""
    if status in (
        CustomMarketplaceRequestStatus.OPEN,
        CustomMarketplaceRequestStatus.UNDER_REVIEW,
    ):
        if proposed_count == 0:
            return "Încă nu există oferte de la furnizori înregistrate pentru această cerere."
        if proposed_count == 1:
            return "A fost primită o ofertă de la un furnizor și poate fi în analiză."
        return f"Au fost primite {proposed_count} oferte de la furnizori și pot fi în analiză."
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return (
            "Echipa a selectat o ofertă de la furnizor. Pașii următori depind de cazul tău și "
            "de legătura de rezervare de la echipă."
        )
    if status in (
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
        CustomMarketplaceRequestStatus.FULFILLED,
    ):
        return "Această cerere a fost gestionată cu asistență din partea echipei."
    if status == CustomMarketplaceRequestStatus.CLOSED_EXTERNAL:
        return "Această cerere a fost închisă în afara fluxului de checkout din aplicație."
    if status == CustomMarketplaceRequestStatus.CANCELLED:
        return ""
    return ""


def _customer_selected_offer_summary(
    session: Session,
    *,
    row: CustomMarketplaceRequest,
) -> MiniAppSelectedOfferSummaryRead | None:
    """Allowlisted snippet for the admin-selected proposed response only."""
    sel_id = row.selected_supplier_response_id
    if sel_id is None:
        return None
    if row.status not in (
        CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
        CustomMarketplaceRequestStatus.FULFILLED,
    ):
        return None
    resp = session.get(SupplierCustomRequestResponse, sel_id)
    if resp is None or resp.request_id != row.id:
        return None
    if resp.response_kind != SupplierCustomRequestResponseKind.PROPOSED:
        return None
    excerpt: str | None = None
    if resp.supplier_message:
        one_line = " ".join(resp.supplier_message.split())
        if one_line:
            excerpt = one_line[:_CUSTOMER_OFFER_MESSAGE_EXCERPT_MAX]
    price: Decimal | None = resp.quoted_price
    currency = (resp.quoted_currency or "").strip() or None
    return MiniAppSelectedOfferSummaryRead(
        quoted_price=price,
        quoted_currency=currency,
        supplier_message_excerpt=excerpt,
        declared_sales_mode=(
            resp.supplier_declared_sales_mode.value if resp.supplier_declared_sales_mode else None
        ),
        declared_payment_mode=(
            resp.supplier_declared_payment_mode.value
            if resp.supplier_declared_payment_mode
            else None
        ),
    )


class CustomMarketplaceRequestService:
    def __init__(self) -> None:
        self._requests = CustomMarketplaceRequestRepository()
        self._responses = SupplierCustomRequestResponseRepository()
        self._users = UserRepository()

    def _read_with_operational_list_hints(self, row: CustomMarketplaceRequest, session: Session) -> CustomMarketplaceRequestRead:
        counts = self._responses.count_proposed_for_requests(session, request_ids=[row.id])
        hints = build_operational_list_hints(
            status=row.status,
            request_type=row.request_type,
            travel_date_start=row.travel_date_start,
            travel_date_end=row.travel_date_end,
            group_size=row.group_size,
            route_notes=row.route_notes,
            proposed_supplier_response_count=counts.get(row.id, 0),
            selected_supplier_response_id=row.selected_supplier_response_id,
        )
        base = CustomMarketplaceRequestRead.model_validate(row, from_attributes=True)
        tg = row.user.telegram_user_id if row.user is not None else None
        cs = build_admin_customer_summary_from_user(row.user)
        return base.model_copy(
            update={
                "operational_hints": hints,
                "customer_telegram_user_id": tg,
                "customer_summary": cs,
            },
        )

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
        ids = [r.id for r in rows]
        counts = self._responses.count_proposed_for_requests(session, request_ids=ids)
        out: list[CustomMarketplaceRequestRead] = []
        for r in rows:
            hints = build_operational_list_hints(
                status=r.status,
                request_type=r.request_type,
                travel_date_start=r.travel_date_start,
                travel_date_end=r.travel_date_end,
                group_size=r.group_size,
                route_notes=r.route_notes,
                proposed_supplier_response_count=counts.get(r.id, 0),
                selected_supplier_response_id=r.selected_supplier_response_id,
            )
            base = CustomMarketplaceRequestRead.model_validate(r, from_attributes=True)
            out.append(
                base.model_copy(
                    update={
                        "customer_telegram_user_id": r.user.telegram_user_id if r.user is not None else None,
                        "customer_summary": build_admin_customer_summary_from_user(r.user),
                        "operational_hints": hints,
                    },
                )
            )
        return out

    def get_admin_detail(self, session: Session, *, request_id: int) -> CustomMarketplaceRequestDetailRead:
        row = self._requests.get_with_responses(session, request_id=request_id)
        if row is None:
            raise CustomMarketplaceRequestNotFoundError
        sel_id = row.selected_supplier_response_id
        responses = [_response_read(r, selected_supplier_response_id=sel_id) for r in row.supplier_responses]
        tg = row.user.telegram_user_id if row.user is not None else None
        bridge = CustomRequestBookingBridgeService().read_for_admin_detail(session, request_id=request_id)
        effective = None
        if bridge is not None and bridge.tour_id is not None and sel_id is not None:
            tour = session.get(Tour, bridge.tour_id)
            sel_resp = session.get(SupplierCustomRequestResponse, sel_id)
            if tour is not None and sel_resp is not None:
                effective = EffectiveCommercialExecutionPolicyService.resolve(
                    tour=tour,
                    request=row,
                    response=sel_resp,
                )
        proposed_count = self._responses.count_proposed_for_request(session, request_id=row.id)
        op_detail = build_operational_detail_hints(
            status=row.status,
            request_type=row.request_type,
            travel_date_start=row.travel_date_start,
            travel_date_end=row.travel_date_end,
            group_size=row.group_size,
            route_notes=row.route_notes,
            proposed_supplier_response_count=proposed_count,
            selected_supplier_response_id=row.selected_supplier_response_id,
            booking_bridge=bridge,
            commercial_resolution_kind=row.commercial_resolution_kind,
        )
        bridge_status_for_preview = bridge.bridge_status if bridge is not None else None
        preferred_lang = row.user.preferred_language if row.user is not None else None
        prepared_msg = CustomRequestLifecyclePreviewService().admin_prepared_lifecycle_message(
            session,
            request_id=row.id,
            bridge_status=bridge_status_for_preview,
            language_code=preferred_lang,
        )
        return CustomMarketplaceRequestDetailRead(
            request=CustomMarketplaceRequestRead.model_validate(row, from_attributes=True).model_copy(
                update={
                    "customer_telegram_user_id": tg,
                    "customer_summary": build_admin_customer_summary_from_user(row.user),
                },
            ),
            responses=responses,
            customer_telegram_user_id=tg,
            booking_bridge=bridge,
            effective_execution_policy=effective,
            operational_hints=op_detail,
            prepared_customer_lifecycle_message=prepared_msg,
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
        return self._read_with_operational_list_hints(row, session)

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
        return self._read_with_operational_list_hints(row, session)

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
        out: list[CustomMarketplaceRequestRead] = []
        for r in rows:
            hints = build_supplier_portal_hints(
                session,
                row=r,
                supplier_id=supplier_id,
                response_repository=self._responses,
            )
            base = CustomMarketplaceRequestRead.model_validate(r, from_attributes=True)
            out.append(base.model_copy(update={"supplier_portal_hints": hints}))
        return out

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
        hints = build_supplier_portal_hints(
            session,
            row=row,
            supplier_id=supplier_id,
            response_repository=self._responses,
        )
        req_read = CustomMarketplaceRequestRead.model_validate(row, from_attributes=True).model_copy(
            update={"supplier_portal_hints": hints},
        )
        return CustomMarketplaceRequestDetailRead(
            request=req_read,
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
        decl_sales: TourSalesMode | None = None
        decl_pay: SupplierOfferPaymentMode | None = None
        if payload.response_kind == SupplierCustomRequestResponseKind.DECLINED:
            msg = (msg or "").strip() or None
        else:
            decl_sales = payload.supplier_declared_sales_mode
            decl_pay = payload.supplier_declared_payment_mode
        row = self._responses.upsert(
            session,
            request_id=request_id,
            supplier_id=supplier_id,
            response_kind=payload.response_kind,
            supplier_message=msg,
            quoted_price=payload.quoted_price,
            quoted_currency=payload.quoted_currency,
            supplier_declared_sales_mode=decl_sales,
            supplier_declared_payment_mode=decl_pay,
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
        preview = CustomRequestLifecyclePreviewService()
        items = [
            MiniAppCustomRequestCustomerSummaryRead(
                id=r.id,
                status=r.status,
                request_type=r.request_type,
                travel_date_start=r.travel_date_start,
                travel_date_end=r.travel_date_end,
                created_at=r.created_at,
                group_size=r.group_size,
                route_notes_preview=_customer_route_notes_preview(r),
                customer_visible_summary=customer_visible_summary(r),
                activity_preview_title=preview.list_activity_title(
                    session,
                    request_id=r.id,
                    language_code=user.preferred_language,
                ),
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
        latest_bridge = CustomRequestBookingBridgeRepository().get_latest_for_request(
            session,
            request_id=row.id,
        )
        bridge_status = None
        bridge_tour_code: str | None = None
        if latest_bridge is not None:
            bridge_status = latest_bridge.bridge_status
            if latest_bridge.tour_id is not None:
                tour = session.get(Tour, latest_bridge.tour_id)
                if tour is not None:
                    bridge_tour_code = tour.code
        proposed_count = self._responses.count_proposed_for_request(session, request_id=row.id)
        offers_hint = _customer_offers_received_hint(
            status=row.status,
            proposed_count=proposed_count,
            language_code=user.preferred_language,
        )
        selected_snippet = _customer_selected_offer_summary(session, row=row)
        activity = CustomRequestLifecyclePreviewService().detail_activity_preview(
            session,
            request_id=row.id,
            bridge_status=bridge_status,
            language_code=user.preferred_language,
        )
        return MiniAppCustomRequestCustomerDetailRead(
            id=row.id,
            status=row.status,
            created_at=row.created_at,
            route_notes=row.route_notes,
            customer_visible_summary=customer_visible_summary(row),
            commercial_mode=CustomerCommercialMode.CUSTOM_BUS_RENTAL_REQUEST,
            request_type=row.request_type,
            travel_date_start=row.travel_date_start,
            travel_date_end=row.travel_date_end,
            group_size=row.group_size,
            route_notes_preview=_customer_route_notes_preview(row),
            latest_booking_bridge_status=bridge_status,
            latest_booking_bridge_tour_code=bridge_tour_code,
            proposed_response_count=proposed_count,
            offers_received_hint=offers_hint,
            selected_offer_summary=selected_snippet,
            activity_preview=activity,
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
        supplier_declared_sales_mode=row.supplier_declared_sales_mode,
        supplier_declared_payment_mode=row.supplier_declared_payment_mode,
        is_selected=is_selected,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
