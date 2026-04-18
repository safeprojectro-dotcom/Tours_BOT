"""X1/X2: supplier portal readability and response-workflow copy — safe only (no admin operational hints)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.custom_marketplace_request import CustomMarketplaceRequest
from app.models.enums import (
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    SupplierCustomRequestResponseKind,
)
from app.repositories.custom_marketplace import SupplierCustomRequestResponseRepository
from app.schemas.custom_marketplace import (
    SupplierPortalRequestHintsRead,
    SupplierPortalResponseWorkflowHintsRead,
)

_REQUEST_TYPE_LABEL: dict[CustomMarketplaceRequestType, str] = {
    CustomMarketplaceRequestType.GROUP_TRIP: "Group trip",
    CustomMarketplaceRequestType.CUSTOM_ROUTE: "Custom route",
    CustomMarketplaceRequestType.OTHER: "Other request",
}

_ROUTE_EXCERPT_MAX = 120


def _request_type_label(rt: CustomMarketplaceRequestType) -> str:
    return _REQUEST_TYPE_LABEL.get(rt, "Custom request")


def _supplier_request_summary_line(row: CustomMarketplaceRequest) -> str:
    label = _request_type_label(row.request_type)
    if row.travel_date_end:
        dates = f"{row.travel_date_start} → {row.travel_date_end}"
    else:
        dates = str(row.travel_date_start)
    parts: list[str] = [label, dates]
    if row.group_size is not None:
        parts.append(f"up to {row.group_size} travellers")
    rn = (row.route_notes or "").strip()
    if rn:
        one = " ".join(rn.split())
        excerpt = one[:_ROUTE_EXCERPT_MAX] + ("…" if len(one) > _ROUTE_EXCERPT_MAX else "")
        parts.append(excerpt)
    return " · ".join(parts)


def _customer_need_summary(row: CustomMarketplaceRequest) -> str:
    """Plain supplier-facing 'what they are asking for' from structured fields only."""
    label = _request_type_label(row.request_type)
    route = (row.route_notes or "").strip()
    route_part = f" Route / notes: {route}" if route else ""
    dates = (
        f"{row.travel_date_start} → {row.travel_date_end}"
        if row.travel_date_end
        else str(row.travel_date_start)
    )
    size = f" Group size (indicative): {row.group_size}." if row.group_size is not None else ""
    special = (
        f" Special conditions mentioned: {s}." if (s := (row.special_conditions or "").strip()) else ""
    )
    return (
        f"{label} request for travel around {dates}.{size}{route_part}{special}"
    ).strip()


def _build_response_workflow_hints(
    *,
    has_resp: bool,
    kind: str | None,
    selected_mine: bool,
    can_act: bool,
    state: str,
) -> SupplierPortalResponseWorkflowHintsRead:
    """X2: narrative copy only — must stay aligned with existing submit/update rules."""
    if not has_resp:
        wf_state = "none_yet"
        presence = "No response from you is on file in this portal yet."
        kind_expl = (
            "You have not yet saved a proposal (priced offer with the fields this API asks for) or a decline."
        )
        edit = (
            "You may submit a proposal or a decline using the response action for this request."
            if can_act
            else "This request no longer accepts a new supplier response in this portal."
        )
        selection = (
            "Nothing from you is on file yet, so there is no selection involving your offer."
        )
        nxt = (
            "If you can serve the trip, submit a proposal; if not, a decline helps the team move on."
            if can_act
            else "No further supplier steps are expected in this portal for this request."
        )
        return SupplierPortalResponseWorkflowHintsRead(
            your_response_state=wf_state,
            response_presence_one_liner=presence,
            response_kind_explained=kind_expl,
            editability_one_liner=edit,
            selection_meaning_for_supplier=selection,
            what_happens_next=nxt,
        )

    if selected_mine:
        wf_state = "proposal_was_selected"
        presence = "Your proposal is the one marked as selected for this request in the portal."
        kind_expl = (
            "Selection records which offer the team advanced for this RFQ. It is not a payment receipt, "
            "ticket, or travel confirmation — those are handled outside this supplier form."
        )
        edit = "You cannot change your on-record response through this portal; it is view-only here."
        selection = (
            "From the supplier portal perspective, your response-workflow step is complete. "
            "Follow your normal operator channel if they contact you about anything further."
        )
        nxt = (
            "Treat this request as complete in the portal. Do not expect further edits or submissions here "
            "unless the team opens a different process."
        )
        return SupplierPortalResponseWorkflowHintsRead(
            your_response_state=wf_state,
            response_presence_one_liner=presence,
            response_kind_explained=kind_expl,
            editability_one_liner=edit,
            selection_meaning_for_supplier=selection,
            what_happens_next=nxt,
        )

    if not can_act and not selected_mine:
        wf_state = "decline_or_other_read_only"
        if kind == "declined":
            presence = "You previously recorded a decline for this request."
            kind_expl = (
                "A decline means you indicated you would not propose for this request as shown. "
                "The request is no longer open for supplier edits in this portal."
            )
            selection = (
                "Your decline is kept for reference; how the request concluded is handled outside this supplier view."
            )
        else:
            presence = "You have an on-record proposal for this request, but supplier edits are closed here."
            kind_expl = (
                "Your last saved proposal remains for reference. It is not a booking or payment outcome by itself."
            )
            selection = "Another path may have been chosen; this portal view is read-only for your response now."
        edit = "This portal no longer accepts changes to your response for this request."
        nxt = "No further supplier actions are expected here — keep this record if you need it."
        return SupplierPortalResponseWorkflowHintsRead(
            your_response_state=wf_state,
            response_presence_one_liner=presence,
            response_kind_explained=kind_expl,
            editability_one_liner=edit,
            selection_meaning_for_supplier=selection,
            what_happens_next=nxt,
        )

    if kind == "declined":
        wf_state = "decline_on_file"
        presence = "You have recorded a decline for this request."
        kind_expl = (
            "A decline tells the team you are not offering this trip under the request as shown. "
            "You may change to a proposal later while edits are still allowed."
        )
        edit = (
            "You may submit again to replace this decline with a proposal, or leave it on file, "
            "while the request still allows supplier edits."
        )
        selection = (
            "A decline is not selected as a commercial offer; the team may still accept proposals from others."
        )
        if state == "under_review_actionable":
            nxt = (
                "Wait for the review outcome. You may switch to a proposal if your availability changes, "
                "until the request closes to suppliers."
            )
        else:
            nxt = (
                "You may update to a proposal if you can serve the request, or keep the decline on file "
                "while the request stays open."
            )
        return SupplierPortalResponseWorkflowHintsRead(
            your_response_state=wf_state,
            response_presence_one_liner=presence,
            response_kind_explained=kind_expl,
            editability_one_liner=edit,
            selection_meaning_for_supplier=selection,
            what_happens_next=nxt,
        )

    # proposal on file, not selected
    wf_state = "proposal_on_file"
    presence = "You have a priced proposal on file for this request."
    kind_expl = (
        "Your on-record response is a proposal: the structured offer you submitted with price and commercial fields. "
        "It is not a confirmed booking or customer payment by itself."
    )
    edit = (
        "You may submit again to update or replace your proposal while this request still allows supplier edits."
    )
    selection = (
        "The customer team may still compare offers; another supplier may be chosen. "
        "Your proposal stays visible to them until the request closes to suppliers."
    )
    if state == "under_review_actionable":
        nxt = (
            "Wait for the review outcome. Keep your proposal accurate, or update it if your terms change, "
            "while edits are still allowed."
        )
    else:
        nxt = (
            "Wait for team review or update your proposal if your terms change while the request stays open to suppliers."
        )
    return SupplierPortalResponseWorkflowHintsRead(
        your_response_state=wf_state,
        response_presence_one_liner=presence,
        response_kind_explained=kind_expl,
        editability_one_liner=edit,
        selection_meaning_for_supplier=selection,
        what_happens_next=nxt,
    )


def build_supplier_portal_hints(
    session: Session,
    *,
    row: CustomMarketplaceRequest,
    supplier_id: int,
    response_repository: SupplierCustomRequestResponseRepository | None = None,
) -> SupplierPortalRequestHintsRead:
    repo = response_repository or SupplierCustomRequestResponseRepository()
    existing = repo.get_for_supplier(session, request_id=row.id, supplier_id=supplier_id)
    has_resp = existing is not None
    kind: str | None = None
    if existing is not None:
        kind = (
            "proposed"
            if existing.response_kind == SupplierCustomRequestResponseKind.PROPOSED
            else "declined"
        )

    selected_mine = (
        row.selected_supplier_response_id is not None
        and existing is not None
        and row.selected_supplier_response_id == existing.id
    )

    st = row.status
    can_act = st in (
        CustomMarketplaceRequestStatus.OPEN,
        CustomMarketplaceRequestStatus.UNDER_REVIEW,
    )

    if can_act:
        if st == CustomMarketplaceRequestStatus.OPEN:
            state = (
                "open_actionable_no_response_yet"
                if not has_resp
                else "open_actionable_has_response"
            )
        else:
            state = "under_review_actionable"
    elif st == CustomMarketplaceRequestStatus.SUPPLIER_SELECTED:
        state = "read_only_selection_recorded"
    else:
        state = "read_only_closed"

    summary = _supplier_request_summary_line(row)
    need = _customer_need_summary(row)

    if state == "open_actionable_no_response_yet":
        label = "You can respond"
        detail = "Submit a proposal with pricing details, or decline if you cannot serve this request."
        headline = "Open — you have not submitted a response yet."
    elif state == "open_actionable_has_response":
        label = "You can update your response"
        detail = (
            "You already have a saved response. You may update it while this request stays open to suppliers."
        )
        if kind == "declined":
            headline = "Open — you declined; you may change your response while the request stays open."
        else:
            headline = "Open — you submitted an offer; updates are still allowed while open."
    elif state == "under_review_actionable":
        label = "Team is reviewing offers"
        detail = (
            "The customer team may be comparing responses. You can still submit or update your response "
            "until this request is closed to suppliers."
        )
        headline = "Under review — supplier responses may still be updated for now."
    elif state == "read_only_selection_recorded":
        label = "Read only — selection recorded"
        detail = (
            "A proposal was selected for this request. The marketplace form here is no longer used for edits; "
            "follow your normal contact with the team if something changes."
        )
        headline = "Your offer was linked to this request — portal editing is closed (view only)."
    else:
        label = "Read only — closed"
        detail = "This request is closed in the supplier portal. Keep this for your records only."
        headline = "Closed in the portal — view only."

    workflow = _build_response_workflow_hints(
        has_resp=has_resp,
        kind=kind,
        selected_mine=selected_mine,
        can_act=can_act,
        state=state,
    )

    return SupplierPortalRequestHintsRead(
        request_summary_line=summary,
        supplier_visible_headline=headline,
        customer_need_summary=need,
        supplier_has_responded=has_resp,
        supplier_last_response_kind=kind,
        your_response_was_selected=selected_mine,
        can_submit_or_update_response=can_act,
        portal_action_state=state,
        portal_action_state_label=label,
        portal_action_state_detail=detail,
        response_workflow=workflow,
    )
