"""Track 5d: pure helpers for My Requests hub — CTA resolution from existing API shapes (testable without Flet)."""

from __future__ import annotations

from enum import StrEnum

from app.models.enums import (
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
)
from app.schemas.mini_app import (
    MiniAppBookingFacadeState,
    MiniAppBookingListItemRead,
    MiniAppBridgeExecutionPreparationResponse,
    MiniAppBridgePaymentEligibilityRead,
)


class DetailPrimaryCtaKind(StrEnum):
    NONE = "none"
    CONTINUE_TO_PAYMENT = "continue_to_payment"
    CONTINUE_BOOKING = "continue_booking"
    OPEN_BOOKING = "open_booking"


_TERMINAL_BRIDGE_STATUSES: frozenset[CustomRequestBookingBridgeStatus] = frozenset(
    {
        CustomRequestBookingBridgeStatus.SUPERSEDED,
        CustomRequestBookingBridgeStatus.CANCELLED,
    },
)

_TERMINAL_CUSTOMER_REQUEST_STATUSES: frozenset[CustomMarketplaceRequestStatus] = frozenset(
    {
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
        CustomMarketplaceRequestStatus.CANCELLED,
        CustomMarketplaceRequestStatus.FULFILLED,
    },
)


def is_request_status_terminal(status: object) -> bool:
    """U2: customer list grouping — closed / cancelled / fulfilled (not booking terminal)."""
    if not isinstance(status, CustomMarketplaceRequestStatus):
        status = CustomMarketplaceRequestStatus(str(status))
    return status in _TERMINAL_CUSTOMER_REQUEST_STATUSES


def my_requests_list_summary_key(*, n_total: int, n_active: int, n_closed: int) -> str | None:
    """U2: lightweight list-level lifecycle hint (copy only)."""
    if n_total <= 0:
        return None
    if n_closed == n_total:
        return "my_requests_list_summary_all_closed"
    if n_active == n_total:
        return "my_requests_list_summary_all_active"
    return "my_requests_list_summary_mixed"


def my_requests_row_hint_key(status: object) -> str:
    """U2: per-row hint shell key (resolved via mini_app.ui_strings.shell)."""
    if not isinstance(status, CustomMarketplaceRequestStatus):
        status = CustomMarketplaceRequestStatus(str(status))
    return {
        CustomMarketplaceRequestStatus.OPEN: "my_requests_row_hint_open",
        CustomMarketplaceRequestStatus.UNDER_REVIEW: "my_requests_row_hint_under_review",
        CustomMarketplaceRequestStatus.SUPPLIER_SELECTED: "my_requests_row_hint_supplier_selected",
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED: "my_requests_row_hint_closed_assisted",
        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL: "my_requests_row_hint_closed_external",
        CustomMarketplaceRequestStatus.CANCELLED: "my_requests_row_hint_cancelled",
        CustomMarketplaceRequestStatus.FULFILLED: "my_requests_row_hint_fulfilled",
    }.get(status, "my_requests_row_hint_open")


def detail_next_step_key(*, status: object, cta_kind: DetailPrimaryCtaKind) -> str:
    """U2: one conservative next-step line; when a CTA exists, align copy with that action only."""
    if not isinstance(status, CustomMarketplaceRequestStatus):
        status = CustomMarketplaceRequestStatus(str(status))
    if cta_kind == DetailPrimaryCtaKind.CONTINUE_TO_PAYMENT:
        return "my_requests_detail_next_pay_when_ready"
    if cta_kind == DetailPrimaryCtaKind.CONTINUE_BOOKING:
        return "my_requests_detail_next_continue_booking"
    if cta_kind == DetailPrimaryCtaKind.OPEN_BOOKING:
        return "my_requests_detail_next_open_booking"
    if status == CustomMarketplaceRequestStatus.CANCELLED:
        return "my_requests_detail_next_cancelled"
    if status in (
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
        CustomMarketplaceRequestStatus.FULFILLED,
    ):
        return "my_requests_detail_next_closed"
    if status == CustomMarketplaceRequestStatus.OPEN:
        return "my_requests_detail_next_open"
    if status == CustomMarketplaceRequestStatus.UNDER_REVIEW:
        return "my_requests_detail_next_under_review"
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return "my_requests_detail_next_supplier_selected"
    return "my_requests_detail_next_generic"


def request_status_lists_action_followup(status: CustomMarketplaceRequestStatus) -> bool:
    """List row hint: supplier-side resolution may allow a next step (detail + bridge checks)."""
    return status in (
        CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
    )


def pick_booking_for_bridge_tour(
    items: list[MiniAppBookingListItemRead],
    tour_code: str,
) -> MiniAppBookingListItemRead | None:
    """Prefer active temporary hold on linked tour; else any booking row for that tour."""
    for it in items:
        if it.summary.tour.code != tour_code:
            continue
        if it.facade_state == MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION:
            return it
    for it in items:
        if it.summary.tour.code == tour_code:
            return it
    return None


def resolve_detail_primary_cta(
    *,
    prep: MiniAppBridgeExecutionPreparationResponse | None,
    payment_elig: MiniAppBridgePaymentEligibilityRead | None,
    hold_order_id: int | None,
    matching_booking: MiniAppBookingListItemRead | None,
    latest_booking_bridge_status: CustomRequestBookingBridgeStatus | None = None,
) -> tuple[DetailPrimaryCtaKind, int | None]:
    """
    Single dominant CTA for request detail. Uses only client-assembled facts from existing endpoints.

    Payment: requires bridge context (prep not None), eligibility read, and hold order id.
    Continue booking: bridge prep allows self-service preparation.
    Open booking: existing Layer A row for linked tour (e.g. confirmed trip or non-payable hold).
    """
    bridge_terminal = (
        latest_booking_bridge_status in _TERMINAL_BRIDGE_STATUSES
        if latest_booking_bridge_status is not None
        else False
    )
    pay_order: int | None = None
    if payment_elig is not None and payment_elig.payment_entry_allowed:
        pay_order = payment_elig.order_id or hold_order_id
    if (
        prep is not None
        and payment_elig is not None
        and payment_elig.payment_entry_allowed
        and pay_order is not None
    ):
        return DetailPrimaryCtaKind.CONTINUE_TO_PAYMENT, pay_order

    if matching_booking is not None and matching_booking.facade_state in (
        MiniAppBookingFacadeState.CONFIRMED,
        MiniAppBookingFacadeState.IN_TRIP_PIPELINE,
    ):
        return DetailPrimaryCtaKind.OPEN_BOOKING, matching_booking.summary.order.id

    if (
        bridge_terminal
        and matching_booking is not None
        and matching_booking.facade_state == MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION
    ):
        return (
            DetailPrimaryCtaKind.CONTINUE_TO_PAYMENT,
            matching_booking.summary.order.id,
        )

    if prep is not None and prep.self_service_available:
        return DetailPrimaryCtaKind.CONTINUE_BOOKING, None

    if matching_booking is not None:
        return DetailPrimaryCtaKind.OPEN_BOOKING, matching_booking.summary.order.id

    return DetailPrimaryCtaKind.NONE, None


def detail_context_line_keys(
    *,
    prep: MiniAppBridgeExecutionPreparationResponse | None,
    prep_http_not_found: bool,
    latest_booking_bridge_status: CustomRequestBookingBridgeStatus | None = None,
) -> tuple[str | None, str | None]:
    """
    Returns (i18n key for status line, optional i18n key for secondary hint).
    Keys are resolved via mini_app.ui_strings.shell.
    """
    if latest_booking_bridge_status in _TERMINAL_BRIDGE_STATUSES:
        return ("rfq_hub_detail_bridge_closed", None)
    if prep_http_not_found or prep is None:
        return ("rfq_hub_detail_no_bridge", None)
    if prep.self_service_available:
        return ("rfq_hub_detail_self_service_yes", None)
    return ("rfq_hub_detail_self_service_no", None)


_REQUEST_STATUS_SHELL_KEYS: dict[CustomMarketplaceRequestStatus, str] = {
    CustomMarketplaceRequestStatus.OPEN: "rfq_status_open",
    CustomMarketplaceRequestStatus.UNDER_REVIEW: "rfq_status_under_review",
    CustomMarketplaceRequestStatus.SUPPLIER_SELECTED: "rfq_status_supplier_selected",
    CustomMarketplaceRequestStatus.CLOSED_ASSISTED: "rfq_status_closed_assisted",
    CustomMarketplaceRequestStatus.CLOSED_EXTERNAL: "rfq_status_closed_external",
    CustomMarketplaceRequestStatus.CANCELLED: "rfq_status_cancelled",
    CustomMarketplaceRequestStatus.FULFILLED: "rfq_status_fulfilled",
}

_REQUEST_TYPE_SHELL_KEYS: dict[CustomMarketplaceRequestType, str] = {
    CustomMarketplaceRequestType.GROUP_TRIP: "rfq_type_group_trip",
    CustomMarketplaceRequestType.CUSTOM_ROUTE: "rfq_type_custom_route",
    CustomMarketplaceRequestType.OTHER: "rfq_type_other",
}


def request_status_user_label(lang: str | None, status: object) -> str:
    from mini_app.ui_strings import shell

    if not isinstance(status, CustomMarketplaceRequestStatus):
        status = CustomMarketplaceRequestStatus(str(status))
    key = _REQUEST_STATUS_SHELL_KEYS.get(status, "rfq_status_open")
    return shell(lang, key)


def request_type_user_label(lang: str | None, request_type: object) -> str:
    from mini_app.ui_strings import shell

    if not isinstance(request_type, CustomMarketplaceRequestType):
        request_type = CustomMarketplaceRequestType(str(request_type))
    key = _REQUEST_TYPE_SHELL_KEYS.get(request_type, "rfq_type_other")
    return shell(lang, key)
