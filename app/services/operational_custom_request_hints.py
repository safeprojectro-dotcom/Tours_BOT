"""V1–V4: read-side operational hints for admin custom-request views (no new lifecycle semantics).

V2: action_focus, needs_internal_ops_attention, primary_action_hint, bridge_continuation_interpretation.
V3: transition visibility — one-liner (list), selection_link_state, customer_path_visibility, transition_chain_summary (detail).
V4: follow-through posture, progression evidence (not Layer A), follow_through_summary, list one-liner.
"""

from __future__ import annotations

from datetime import date

from app.models.enums import (
    CommercialResolutionKind,
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
)
from app.schemas.custom_marketplace import (
    CustomMarketplaceRequestOperationalDetailHintsRead,
    CustomMarketplaceRequestOperationalListHintsRead,
    CustomRequestBookingBridgeRead,
    OperationalActionFocusRead,
    OperationalCustomerPathVisibilityRead,
    OperationalCustomerProgressionEvidenceRead,
    OperationalFollowThroughPostureRead,
    OperationalSelectionLinkRead,
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


def _list_follow_through_one_liner(*, status: CustomMarketplaceRequestStatus) -> str:
    """V4: lightweight list hint — detail has follow_through_summary."""
    if operational_is_terminal_status(status):
        return "Follow-through: terminal — no onward customer path expected in this record."
    if status in (
        CustomMarketplaceRequestStatus.OPEN,
        CustomMarketplaceRequestStatus.UNDER_REVIEW,
    ):
        return "Follow-through: not at customer execution yet — commercial steps come first."
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return "Follow-through: after selection — real progression only on detail (bridge + evidence level)."
    return "Follow-through: see detail."


def _follow_through_posture(
    *,
    status: CustomMarketplaceRequestStatus,
    sel_link: OperationalSelectionLinkRead,
    cust_vis: OperationalCustomerPathVisibilityRead,
    bridge: CustomRequestBookingBridgeRead | None,
) -> OperationalFollowThroughPostureRead:
    """V4: stalled vs progressing vs terminal — from RFQ + bridge row only."""
    if operational_is_terminal_status(status):
        return OperationalFollowThroughPostureRead.TERMINAL_CLOSED
    if sel_link == OperationalSelectionLinkRead.CLOSED_RECORD:
        return OperationalFollowThroughPostureRead.TERMINAL_CLOSED
    if sel_link == OperationalSelectionLinkRead.PRE_COMMERCIAL_DECISION:
        return OperationalFollowThroughPostureRead.PRE_CUSTOMER_EXECUTION
    if sel_link == OperationalSelectionLinkRead.SELECTION_DATA_INCOMPLETE:
        return OperationalFollowThroughPostureRead.SELECTION_DATA_GAP
    if sel_link == OperationalSelectionLinkRead.SELECTED_RESPONSE_ON_FILE:
        if cust_vis == OperationalCustomerPathVisibilityRead.NO_CUSTOMER_PATH_LINKED:
            return OperationalFollowThroughPostureRead.COMMERCIAL_WITHOUT_BRIDGE
        if cust_vis == OperationalCustomerPathVisibilityRead.BRIDGE_NOT_ACTIVE:
            return OperationalFollowThroughPostureRead.BRIDGE_INACTIVE_STALLED
        if cust_vis == OperationalCustomerPathVisibilityRead.BRIDGE_PREP_ONLY:
            return OperationalFollowThroughPostureRead.BRIDGE_AWAITING_CLEARANCE
        if cust_vis == OperationalCustomerPathVisibilityRead.CUSTOMER_CONTINUATION_MAY_EXIST:
            if (
                bridge is not None
                and bridge.bridge_status == CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED
            ):
                return OperationalFollowThroughPostureRead.NOTIFY_MILESTONE_NO_COMPLETION_EVIDENCE
            return OperationalFollowThroughPostureRead.PATH_MAY_EXIST_NO_PROGRESSION_EVIDENCE_HERE
    return OperationalFollowThroughPostureRead.PRE_CUSTOMER_EXECUTION


def _customer_progression_evidence(
    *,
    status: CustomMarketplaceRequestStatus,
    sel_link: OperationalSelectionLinkRead,
    cust_vis: OperationalCustomerPathVisibilityRead,
    bridge: CustomRequestBookingBridgeRead | None,
) -> OperationalCustomerProgressionEvidenceRead:
    """V4: explicit separation of path availability vs proof of customer movement."""
    if operational_is_terminal_status(status):
        return OperationalCustomerProgressionEvidenceRead.TERMINAL_NO_FURTHER_EVIDENCE_EXPECTED
    if sel_link == OperationalSelectionLinkRead.PRE_COMMERCIAL_DECISION:
        return OperationalCustomerProgressionEvidenceRead.NOT_APPLICABLE
    if sel_link == OperationalSelectionLinkRead.SELECTION_DATA_INCOMPLETE:
        return OperationalCustomerProgressionEvidenceRead.NO_CUSTOMER_PATH_VISIBLE
    if cust_vis == OperationalCustomerPathVisibilityRead.NOT_YET_APPLICABLE:
        return OperationalCustomerProgressionEvidenceRead.NOT_APPLICABLE
    if cust_vis == OperationalCustomerPathVisibilityRead.TERMINAL_NO_FORWARD_PATH:
        return OperationalCustomerProgressionEvidenceRead.TERMINAL_NO_FURTHER_EVIDENCE_EXPECTED
    if cust_vis == OperationalCustomerPathVisibilityRead.NO_CUSTOMER_PATH_LINKED:
        return OperationalCustomerProgressionEvidenceRead.NO_CUSTOMER_PATH_VISIBLE
    if cust_vis == OperationalCustomerPathVisibilityRead.BRIDGE_NOT_ACTIVE:
        return OperationalCustomerProgressionEvidenceRead.NO_CUSTOMER_PATH_VISIBLE
    if cust_vis == OperationalCustomerPathVisibilityRead.BRIDGE_PREP_ONLY:
        return OperationalCustomerProgressionEvidenceRead.NO_BOOKING_OR_PAYMENT_EVIDENCE_IN_THIS_VIEW
    if cust_vis == OperationalCustomerPathVisibilityRead.CUSTOMER_CONTINUATION_MAY_EXIST:
        if (
            bridge is not None
            and bridge.bridge_status == CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED
        ):
            return OperationalCustomerProgressionEvidenceRead.NOTIFICATION_MILESTONE_ONLY
        return OperationalCustomerProgressionEvidenceRead.NO_BOOKING_OR_PAYMENT_EVIDENCE_IN_THIS_VIEW
    return OperationalCustomerProgressionEvidenceRead.NO_BOOKING_OR_PAYMENT_EVIDENCE_IN_THIS_VIEW


def _follow_through_summary(
    *,
    posture: OperationalFollowThroughPostureRead,
) -> str:
    """V4: concise ops narrative — never implies paid/completed booking."""
    if posture == OperationalFollowThroughPostureRead.TERMINAL_CLOSED:
        return (
            "Follow-through is closed from this request record’s perspective — no further customer path is expected "
            "here. Verify trip outcomes in Layer A / bookings if needed."
        )
    if posture == OperationalFollowThroughPostureRead.PRE_CUSTOMER_EXECUTION:
        return (
            "Not yet at linked customer execution: follow-through is still before a stable in-app path. "
            "Commercial resolution and (when used) bridge creation are the usual prerequisites."
        )
    if posture == OperationalFollowThroughPostureRead.SELECTION_DATA_GAP:
        return (
            "Follow-through cannot be trusted until selection data is consistent — reconcile status vs selected "
            "response id before judging stalls or customer movement."
        )
    if posture == OperationalFollowThroughPostureRead.COMMERCIAL_WITHOUT_BRIDGE:
        return (
            "Commercial selection exists without a booking bridge — a common stall: in-app customer follow-through "
            "is not linked until a bridge exists or work moves off-platform explicitly."
        )
    if posture == OperationalFollowThroughPostureRead.BRIDGE_AWAITING_CLEARANCE:
        return (
            "Bridge is present but not clearance-complete — treat customer-facing follow-through as not reliably open "
            "yet; expect no proven customer movement from this view alone."
        )
    if posture == OperationalFollowThroughPostureRead.BRIDGE_INACTIVE_STALLED:
        return (
            "Execution bridge is inactive (ended/replaced) — follow-through stalls for the linked in-app path until "
            "a new bridge or an external continuation is established."
        )
    if posture == OperationalFollowThroughPostureRead.NOTIFY_MILESTONE_NO_COMPLETION_EVIDENCE:
        return (
            "A customer-notification milestone exists on the bridge; that records an ops step, not booking, hold, "
            "or payment. Check Layer A for real customer progression."
        )
    if posture == OperationalFollowThroughPostureRead.PATH_MAY_EXIST_NO_PROGRESSION_EVIDENCE_HERE:
        return (
            "Customer path may be available in the app when policies allow, but this RFQ admin view carries no "
            "booking or payment evidence — assume follow-through unproven until confirmed outside this snapshot."
        )
    return (
        "Use posture, bridge status, and Layer A tooling together — this summary is interpretive read-side text only."
    )


def _list_transition_one_liner(*, status: CustomMarketplaceRequestStatus) -> str:
    """V3: single scan-friendly line; detail carries full transition_chain_summary."""
    if operational_is_terminal_status(status):
        return (
            "Transition: closed in system — use detail for audit; no forward in-app chain implied here."
        )
    if status in (
        CustomMarketplaceRequestStatus.OPEN,
        CustomMarketplaceRequestStatus.UNDER_REVIEW,
    ):
        return (
            "Transition: before commercial selection — bridge and customer path follow resolution."
        )
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return "Transition: after selection — bridge + customer path on detail."
    return "Transition: see detail for full chain."


def _operational_selection_link(
    *,
    status: CustomMarketplaceRequestStatus,
    selected_supplier_response_id: int | None,
) -> OperationalSelectionLinkRead:
    if operational_is_terminal_status(status):
        return OperationalSelectionLinkRead.CLOSED_RECORD
    if status in (
        CustomMarketplaceRequestStatus.OPEN,
        CustomMarketplaceRequestStatus.UNDER_REVIEW,
    ):
        return OperationalSelectionLinkRead.PRE_COMMERCIAL_DECISION
    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        if selected_supplier_response_id is None:
            return OperationalSelectionLinkRead.SELECTION_DATA_INCOMPLETE
        return OperationalSelectionLinkRead.SELECTED_RESPONSE_ON_FILE
    return OperationalSelectionLinkRead.PRE_COMMERCIAL_DECISION


def _operational_customer_path_visibility(
    *,
    status: CustomMarketplaceRequestStatus,
    selected_supplier_response_id: int | None,
    bridge: CustomRequestBookingBridgeRead | None,
) -> OperationalCustomerPathVisibilityRead:
    if operational_is_terminal_status(status):
        return OperationalCustomerPathVisibilityRead.TERMINAL_NO_FORWARD_PATH
    if status in (
        CustomMarketplaceRequestStatus.OPEN,
        CustomMarketplaceRequestStatus.UNDER_REVIEW,
    ):
        return OperationalCustomerPathVisibilityRead.NOT_YET_APPLICABLE
    if status != CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        return OperationalCustomerPathVisibilityRead.NOT_YET_APPLICABLE
    if selected_supplier_response_id is None:
        return OperationalCustomerPathVisibilityRead.NO_CUSTOMER_PATH_LINKED
    if bridge is None:
        return OperationalCustomerPathVisibilityRead.NO_CUSTOMER_PATH_LINKED
    bst = bridge.bridge_status
    if bst in (
        CustomRequestBookingBridgeStatus.SUPERSEDED,
        CustomRequestBookingBridgeStatus.CANCELLED,
    ):
        return OperationalCustomerPathVisibilityRead.BRIDGE_NOT_ACTIVE
    if bst == CustomRequestBookingBridgeStatus.PENDING_VALIDATION:
        return OperationalCustomerPathVisibilityRead.BRIDGE_PREP_ONLY
    if bst in (
        CustomRequestBookingBridgeStatus.READY,
        CustomRequestBookingBridgeStatus.LINKED_TOUR,
        CustomRequestBookingBridgeStatus.CUSTOMER_NOTIFIED,
    ):
        return OperationalCustomerPathVisibilityRead.CUSTOMER_CONTINUATION_MAY_EXIST
    return OperationalCustomerPathVisibilityRead.BRIDGE_PREP_ONLY


def _transition_chain_summary(
    *,
    status: CustomMarketplaceRequestStatus,
    commercial_resolution_kind: CommercialResolutionKind | None,
    selection_link: OperationalSelectionLinkRead,
    customer_vis: OperationalCustomerPathVisibilityRead,
    bridge: CustomRequestBookingBridgeRead | None,
    proposed_count: int,
) -> str:
    """V3: narrative only — does not assert payment, customer action, or live bridge authority."""
    if operational_is_terminal_status(status):
        parts: list[str] = []
        if status == CustomMarketplaceRequestStatus.CLOSED_ASSISTED:
            parts.append("Terminal: assisted closure recorded.")
        elif status == CustomMarketplaceRequestStatus.CLOSED_EXTERNAL:
            parts.append("Terminal: external / off automated checkout record.")
        elif status == CustomMarketplaceRequestStatus.CANCELLED:
            parts.append("Terminal: cancelled — no forward commercial chain in this system.")
        else:
            parts.append("Terminal: legacy/fulfilled-style closed record.")
        if commercial_resolution_kind is not None:
            parts.append(f"Commercial resolution kind on file: {commercial_resolution_kind.value}.")
        if bridge is not None:
            parts.append(
                "A booking bridge row may still appear — treat as potentially historical; confirm active path separately."
            )
        return " ".join(parts)

    if status in (
        CustomMarketplaceRequestStatus.OPEN,
        CustomMarketplaceRequestStatus.UNDER_REVIEW,
    ):
        return (
            f"Chain: intake/review — {proposed_count} proposed supplier offer(s). "
            "Commercial selection and bridge are downstream; customer Mini App continuation is not in play yet."
        )

    if status == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        if selection_link == OperationalSelectionLinkRead.SELECTION_DATA_INCOMPLETE:
            return (
                "Chain blocked for interpretation: status says selection but selected response id is missing — "
                "reconcile before trusting bridge or customer visibility."
            )
        seg: list[str] = ["Chain: commercial selection applied (winning response id on file)."]
        if bridge is None:
            seg.append(
                "Bridge: absent — selection is not yet linked to in-app customer execution; create bridge when intended."
            )
        else:
            seg.append(
                f"Bridge: row exists ({bridge.bridge_status.value}) — links intent to tour/user context; "
                "Layer A hold/payment remains separate."
            )
        if customer_vis == OperationalCustomerPathVisibilityRead.CUSTOMER_CONTINUATION_MAY_EXIST:
            seg.append(
                "Customer: in-app continuation may be offered when existing prep APIs allow — not proof the customer "
                "acted or paid."
            )
        elif customer_vis == OperationalCustomerPathVisibilityRead.BRIDGE_PREP_ONLY:
            seg.append(
                "Customer: still in bridge prep/validation — do not assume customer-visible next steps yet."
            )
        elif customer_vis == OperationalCustomerPathVisibilityRead.BRIDGE_NOT_ACTIVE:
            seg.append(
                "Customer: prior bridge inactive — replacement bridge or off-platform path must be explicit."
            )
        elif customer_vis == OperationalCustomerPathVisibilityRead.NO_CUSTOMER_PATH_LINKED:
            seg.append("Customer: no linked in-app path from this record state yet.")
        return " ".join(seg)

    return "Chain: use lifecycle status, supplier responses, and bridge rows together."


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
        transition_stage_one_liner=_list_transition_one_liner(status=status),
        follow_through_one_liner=_list_follow_through_one_liner(status=status),
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
    commercial_resolution_kind: CommercialResolutionKind | None = None,
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
    sel_link = _operational_selection_link(
        status=status,
        selected_supplier_response_id=selected_supplier_response_id,
    )
    cust_vis = _operational_customer_path_visibility(
        status=status,
        selected_supplier_response_id=selected_supplier_response_id,
        bridge=booking_bridge,
    )
    chain_summary = _transition_chain_summary(
        status=status,
        commercial_resolution_kind=commercial_resolution_kind,
        selection_link=sel_link,
        customer_vis=cust_vis,
        bridge=booking_bridge,
        proposed_count=proposed_supplier_response_count,
    )
    ft_posture = _follow_through_posture(
        status=status,
        sel_link=sel_link,
        cust_vis=cust_vis,
        bridge=booking_bridge,
    )
    prog_evidence = _customer_progression_evidence(
        status=status,
        sel_link=sel_link,
        cust_vis=cust_vis,
        bridge=booking_bridge,
    )
    ft_summary = _follow_through_summary(posture=ft_posture)
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
        selection_link_state=sel_link,
        customer_path_visibility=cust_vis,
        transition_chain_summary=chain_summary,
        follow_through_posture=ft_posture,
        customer_progression_evidence=prog_evidence,
        follow_through_summary=ft_summary,
    )
