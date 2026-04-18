"""V1/V2: read-side operational hints for admin custom-request views (no new lifecycle semantics).

V2 adds action_focus, needs_internal_ops_attention, primary_action_hint, and (detail) bridge_continuation_interpretation.
"""

from __future__ import annotations

from datetime import date

from app.models.enums import (
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
)
from app.schemas.custom_marketplace import (
    CustomMarketplaceRequestOperationalDetailHintsRead,
    CustomMarketplaceRequestOperationalListHintsRead,
    CustomRequestBookingBridgeRead,
    OperationalActionFocusRead,
)


_TERMINAL_STATUSES: frozenset[CustomMarketplaceRequestStatus] = frozenset(
    {
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
        CustomMarketplaceRequestStatus.CANCELLED,
        CustomMarketplaceRequestStatus.FULFILLED,
    },
)


def operational_is_terminal_status(status: CustomMarketplaceRequestStatus) -> bool:
    return status in _TERMINAL_STATUSES


def operational_lifecycle_stage_label(status: CustomMarketplaceRequestStatus) -> str:
    return {
        CustomMarketplaceRequestStatus.OPEN: "Intake — open",
        CustomMarketplaceRequestStatus.UNDER_REVIEW: "Review / supplier offers",
        CustomMarketplaceRequestStatus.SUPPLIER_SELECTED: "Commercial selection recorded",
        CustomMarketplaceRequestStatus.CLOSED_ASSISTED: "Closed (assisted)",
        CustomMarketplaceRequestStatus.CLOSED_EXTERNAL: "Closed (external record)",
        CustomMarketplaceRequestStatus.CANCELLED: "Cancelled",
        CustomMarketplaceRequestStatus.FULFILLED: "Fulfilled (legacy)",
    }.get(status, "Unknown status")


def _request_type_short_label(request_type: CustomMarketplaceRequestType) -> str:
    return {
        CustomMarketplaceRequestType.GROUP_TRIP: "Group trip",
        CustomMarketplaceRequestType.CUSTOM_ROUTE: "Custom route",
        CustomMarketplaceRequestType.OTHER: "Other",
    }.get(request_type, "Request")


def _format_travel_dates(travel_date_start: date, travel_date_end: date | None) -> str:
    if travel_date_end is None or travel_date_end == travel_date_start:
        return travel_date_start.isoformat()
    return f"{travel_date_start.isoformat()} → {travel_date_end.isoformat()}"


def _route_preview(route_notes: str, *, max_len: int = 72) -> str:
    one = " ".join((route_notes or "").split())
    if len(one) <= max_len:
        return one or "—"
    return one[: max_len - 1] + "…"


def operational_scan_summary_line(
    *,
    request_type: CustomMarketplaceRequestType,
    travel_date_start: date,
    travel_date_end: date | None,
    group_size: int | None,
    route_notes: str,
) -> str:
    parts: list[str] = [
        _request_type_short_label(request_type),
        _format_travel_dates(travel_date_start, travel_date_end),
    ]
    if group_size is not None:
        parts.append(f"group {group_size}")
    parts.append(_route_preview(route_notes))
    return " · ".join(parts)


def _list_action_triple(
    *,
    status: CustomMarketplaceRequestStatus,
    proposed_count: int,
    has_selected_supplier_response: bool,
) -> tuple[OperationalActionFocusRead, bool, str]:
    """V2: list has no bridge — supplier_selected defaults to bridge/setup bucket."""
    if operational_is_terminal_status(status):
        return (
            OperationalActionFocusRead.TERMINAL,
            False,
            "No routine operational action — case is closed in this system.",
        )
    if status == CustomMarketplaceRequestStatus.OPEN:
        if proposed_count == 0:
            return (
                OperationalActionFocusRead.AWAITING_SUPPLIER_PROPOSALS,
                True,
                "Triage intake and obtain proposed supplier offer(s) before a commercial decision.",
            )
        return (
            OperationalActionFocusRead.INTERNAL_REVIEW_OR_RESOLUTION,
            True,
            "Review supplier responses and apply commercial resolution when ready.",
        )
    if status == CustomMarketplaceRequestStatus.UNDER_REVIEW:
        if proposed_count == 0:
            return (
                OperationalActionFocusRead.INTERNAL_REVIEW_OR_RESOLUTION,
                True,
                "Under review but no proposed offers on file — align with suppliers or adjust status.",
            )
        return (
            OperationalActionFocusRead.INTERNAL_REVIEW_OR_RESOLUTION,
            True,
            "Decide commercial direction using the proposed offer(s) and resolution endpoints.",
        )
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        if not has_selected_supplier_response:
            return (
                OperationalActionFocusRead.INTERNAL_REVIEW_OR_RESOLUTION,
                True,
                "Verify selected supplier response id matches records, then manage bridge on the detail view.",
            )
        return (
            OperationalActionFocusRead.BRIDGE_SETUP_OR_VALIDATION,
            True,
            "Commercial selection recorded — open detail to create or inspect the booking bridge.",
        )
    return (
        OperationalActionFocusRead.INTERNAL_REVIEW_OR_RESOLUTION,
        True,
        "Review request fields and supplier responses for the next operational step.",
    )


def _detail_action_triple(
    *,
    status: CustomMarketplaceRequestStatus,
    proposed_count: int,
    has_selected_supplier_response: bool,
    bridge: CustomRequestBookingBridgeRead | None,
) -> tuple[OperationalActionFocusRead, bool, str]:
    """V2: refine list bucket when bridge row is known (detail only)."""
    if operational_is_terminal_status(status):
        return (
            OperationalActionFocusRead.TERMINAL,
            False,
            "No routine operational action — case is closed in this system.",
        )
    if status != CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return _list_action_triple(
            status=status,
            proposed_count=proposed_count,
            has_selected_supplier_response=has_selected_supplier_response,
        )
    if not has_selected_supplier_response:
        return (
            OperationalActionFocusRead.INTERNAL_REVIEW_OR_RESOLUTION,
            True,
            "Verify selected supplier response id matches records, then manage bridge on this view.",
        )
    if bridge is None:
        return (
            OperationalActionFocusRead.BRIDGE_SETUP_OR_VALIDATION,
            True,
            "Create a booking bridge when in-app customer execution should be linked to this selection.",
        )
    bst = bridge.bridge_status
    if bst in (
        CustomRequestBookingBridgeStatus.SUPERSEDED,
        CustomRequestBookingBridgeStatus.CANCELLED,
    ):
        return (
            OperationalActionFocusRead.RECONCILE_CLOSED_BRIDGE,
            True,
            "This bridge row is inactive — decide a replacement bridge or confirm off-platform handling.",
        )
    if bst == CustomRequestBookingBridgeStatus.PENDING_VALIDATION:
        return (
            OperationalActionFocusRead.BRIDGE_SETUP_OR_VALIDATION,
            True,
            "Finish bridge validation / tour linkage before expecting customer execution in the app.",
        )
    if bst in (
        CustomRequestBookingBridgeStatus.READY,
        CustomRequestBookingBridgeStatus.LINKED_TOUR,
        CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED,
    ):
        return (
            OperationalActionFocusRead.MONITOR_CUSTOMER_CONTINUATION,
            False,
            "Customer-side steps (when eligible) use existing Mini App / Layer A flows — monitor bookings; "
            "this summary does not confirm payment or hold state.",
        )
    return (
        OperationalActionFocusRead.BRIDGE_SETUP_OR_VALIDATION,
        True,
        "Inspect booking bridge status and admin notes for the next setup step.",
    )


def _bridge_continuation_interpretation(
    *,
    status: CustomMarketplaceRequestStatus,
    bridge: CustomRequestBookingBridgeRead | None,
) -> str:
    """V2: one line interpreting bridge vs customer path — no payment or eligibility claims."""
    if operational_is_terminal_status(status):
        return "Request is terminal — any bridge below may be historical; do not infer current customer progress from it alone."
    if status != CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return ""
    if bridge is None:
        return (
            "No booking bridge row — customer in-app execution is not linked until an admin creates the bridge."
        )
    bst = bridge.bridge_status
    if bst == CustomRequestBookingBridgeStatus.PENDING_VALIDATION:
        return (
            "Bridge exists but is still pending validation — customer-facing execution is not implied until this clears."
        )
    if bst == CustomRequestBookingBridgeStatus.READY:
        return (
            "Bridge is ready — whether the customer can proceed still depends only on existing prep/payment APIs, "
            "not on this text."
        )
    if bst == CustomRequestBookingBridgeStatus.LINKED_TOUR:
        return (
            "Tour is linked on the bridge — track holds and payment only via Layer A / bookings tools, not here."
        )
    if bst == CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED:
        return (
            "Customer-notified milestone is recorded — check whether they continued in-app or outside; not proof of payment."
        )
    if bst in (
        CustomRequestBookingBridgeStatus.SUPERSEDED,
        CustomRequestBookingBridgeStatus.CANCELLED,
    ):
        return "This bridge record is ended — reconcile whether a new bridge or external path applies."
    return "Review bridge status and linked tour id against your operational checklist."


def bridge_status_operational_label(status: CustomRequestBookingBridgeStatus) -> str:
    """Human-readable bridge row meaning for internal users — not payment eligibility."""
    return {
        CustomRequestBookingBridgeStatus.PENDING_VALIDATION: "Pending validation (tour/link checks)",
        CustomRequestBookingBridgeStatus.READY: "Ready for customer execution context",
        CustomRequestBookingBridgeStatus.LINKED_TOUR: "Tour linked — monitor bookings / customer progress",
        CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED: "Customer-notified step recorded",
        CustomRequestBookingBridgeStatus.SUPERSEDED: "Superseded by a newer bridge",
        CustomRequestBookingBridgeStatus.CANCELLED: "Cancelled / not active",
    }.get(status, status.value)


def _list_handling_hint(
    *,
    status: CustomMarketplaceRequestStatus,
    proposed_count: int,
) -> str:
    if operational_is_terminal_status(status):
        return (
            "Closed in the system — archival reference only; no forward handling here unless your "
            "process reopens the case."
        )
    if status == CustomMarketplaceRequestStatus.OPEN:
        if proposed_count == 0:
            return "New intake — triage and wait for supplier proposals (or follow your outreach process)."
        return (
            f"{proposed_count} proposed supplier offer(s) on file — compare, then move to under review "
            "or apply commercial resolution when ready."
        )
    if status == CustomMarketplaceRequestStatus.UNDER_REVIEW:
        if proposed_count == 0:
            return (
                "Marked under review — no proposed offers recorded yet; align with suppliers or adjust status."
            )
        return (
            f"Under review with {proposed_count} proposed offer(s) — decide selection or next customer contact."
        )
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return (
            "Supplier proposal selected — open detail for booking bridge and how the customer can continue."
        )
    return "Review request fields, responses, and notes for next handling."


def _detail_handling_hint(
    *,
    status: CustomMarketplaceRequestStatus,
    proposed_count: int,
    bridge: CustomRequestBookingBridgeRead | None,
) -> str:
    if operational_is_terminal_status(status):
        return _list_handling_hint(status=status, proposed_count=proposed_count)
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        if bridge is None:
            return (
                "Supplier proposal selected — no booking bridge row on file. Add a bridge when in-app "
                "execution should start, or continue off-platform per your process."
            )
        bl = bridge_status_operational_label(bridge.bridge_status)
        extra = ""
        if bridge.bridge_status in (
            CustomRequestBookingBridgeStatus.SUPERSEDED,
            CustomRequestBookingBridgeStatus.CANCELLED,
        ):
            extra = (
                " This bridge record is terminal — confirm whether a replacement bridge or an external path applies."
            )
        return f"Supplier proposal selected — booking bridge: {bl}.{extra}"
    return _list_handling_hint(status=status, proposed_count=proposed_count)


def _continuation_summary(
    *,
    status: CustomMarketplaceRequestStatus,
    proposed_count: int,
    bridge: CustomRequestBookingBridgeRead | None,
    has_selected_supplier_response: bool,
) -> str:
    if operational_is_terminal_status(status):
        return "Case closed in this system — use status and notes above; bridge rows below may be historical only."
    if status == CustomMarketplaceRequestStatus.OPEN:
        return f"Intake open — {proposed_count} proposed supplier offer(s) on file."
    if status == CustomMarketplaceRequestStatus.UNDER_REVIEW:
        return f"Under review — {proposed_count} proposed supplier offer(s) on file."
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        if not has_selected_supplier_response:
            return "Status shows selection — verify selected response id matches your records."
        if bridge is None:
            return "Commercial selection recorded — no active bridge row; customer app continuation is not wired here yet."
        bl = bridge_status_operational_label(bridge.bridge_status)
        return (
            f"Commercial selection recorded — bridge: {bl}. Customer Mini App steps still follow existing "
            "Layer A rules (not implied as paid or confirmed by this summary)."
        )
    return "See lifecycle status and supplier responses for progress."


def build_operational_list_hints(
    *,
    status: CustomMarketplaceRequestStatus,
    request_type: CustomMarketplaceRequestType,
    travel_date_start: date,
    travel_date_end: date | None,
    group_size: int | None,
    route_notes: str,
    proposed_supplier_response_count: int,
    selected_supplier_response_id: int | None,
) -> CustomMarketplaceRequestOperationalListHintsRead:
    has_sel = selected_supplier_response_id is not None
    focus, need_ops, primary = _list_action_triple(
        status=status,
        proposed_count=proposed_supplier_response_count,
        has_selected_supplier_response=has_sel,
    )
    return CustomMarketplaceRequestOperationalListHintsRead(
        lifecycle_stage_label=operational_lifecycle_stage_label(status),
        is_terminal=operational_is_terminal_status(status),
        scan_summary_line=operational_scan_summary_line(
            request_type=request_type,
            travel_date_start=travel_date_start,
            travel_date_end=travel_date_end,
            group_size=group_size,
            route_notes=route_notes,
        ),
        proposed_supplier_response_count=proposed_supplier_response_count,
        has_selected_supplier_response=has_sel,
        handling_hint=_list_handling_hint(status=status, proposed_count=proposed_supplier_response_count),
        action_focus=focus,
        needs_internal_ops_attention=need_ops,
        primary_action_hint=primary,
    )


def build_operational_detail_hints(
    *,
    status: CustomMarketplaceRequestStatus,
    request_type: CustomMarketplaceRequestType,
    travel_date_start: date,
    travel_date_end: date | None,
    group_size: int | None,
    route_notes: str,
    proposed_supplier_response_count: int,
    selected_supplier_response_id: int | None,
    booking_bridge: CustomRequestBookingBridgeRead | None,
) -> CustomMarketplaceRequestOperationalDetailHintsRead:
    list_part = build_operational_list_hints(
        status=status,
        request_type=request_type,
        travel_date_start=travel_date_start,
        travel_date_end=travel_date_end,
        group_size=group_size,
        route_notes=route_notes,
        proposed_supplier_response_count=proposed_supplier_response_count,
        selected_supplier_response_id=selected_supplier_response_id,
    )
    bridge_label = (
        bridge_status_operational_label(booking_bridge.bridge_status) if booking_bridge is not None else None
    )
    has_sel = selected_supplier_response_id is not None
    dfocus, dneed, dprimary = _detail_action_triple(
        status=status,
        proposed_count=proposed_supplier_response_count,
        has_selected_supplier_response=has_sel,
        bridge=booking_bridge,
    )
    bridge_narrative = _bridge_continuation_interpretation(status=status, bridge=booking_bridge)
    base = list_part.model_dump(
        exclude={"handling_hint", "action_focus", "needs_internal_ops_attention", "primary_action_hint"},
    )
    return CustomMarketplaceRequestOperationalDetailHintsRead(
        **base,
        handling_hint=_detail_handling_hint(
            status=status,
            proposed_count=proposed_supplier_response_count,
            bridge=booking_bridge,
        ),
        action_focus=dfocus,
        needs_internal_ops_attention=dneed,
        primary_action_hint=dprimary,
        booking_bridge_present=booking_bridge is not None,
        booking_bridge_operational_label=bridge_label,
        continuation_summary=_continuation_summary(
            status=status,
            proposed_count=proposed_supplier_response_count,
            bridge=booking_bridge,
            has_selected_supplier_response=has_sel,
        ),
        bridge_continuation_interpretation=bridge_narrative,
    )
