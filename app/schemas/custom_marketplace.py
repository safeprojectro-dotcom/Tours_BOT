"""API schemas for Track 4 custom marketplace (RFQ)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    CommercialResolutionKind,
    CustomerCommercialMode,
    CustomMarketplaceRequestSource,
    CustomMarketplaceRequestStatus,
    CustomMarketplaceRequestType,
    CustomRequestBookingBridgeStatus,
    OperatorWorkflowIntent,
    SupplierCustomRequestResponseKind,
    SupplierOfferPaymentMode,
    TourSalesMode,
)
from app.schemas.admin_customer_summary import AdminCustomerSummary
from app.schemas.custom_request_notification import (
    AdminPreparedCustomRequestLifecycleMessageRead,
    MiniAppCustomRequestActivityPreviewRead,
)
from app.schemas.effective_commercial_execution_policy import EffectiveCommercialExecutionPolicyRead
from app.services.effective_commercial_execution_policy import validate_supplier_declared_rfq_commercial_pair


class MiniAppCustomRequestCreate(BaseModel):
    """Mini App intake: same structured fields as bot path."""

    telegram_user_id: int = Field(gt=0)
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None = None
    route_notes: str = Field(min_length=3, max_length=8000)
    group_size: int | None = Field(default=None, ge=1, le=999)
    special_conditions: str | None = Field(default=None, max_length=8000)

    @field_validator("route_notes", "special_conditions")
    @classmethod
    def strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def date_range_ok(self) -> MiniAppCustomRequestCreate:
        end = self.travel_date_end or self.travel_date_start
        if end < self.travel_date_start:
            raise ValueError("travel_date_end must not be before travel_date_start.")
        return self


class BotCustomRequestCreate(BaseModel):
    """Internal: bot FSM hands off to service with resolved user_id."""

    user_id: int = Field(gt=0)
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None = None
    route_notes: str = Field(min_length=3, max_length=8000)
    group_size: int | None = Field(default=None, ge=1, le=999)
    special_conditions: str | None = Field(default=None, max_length=8000)
    source_channel: CustomMarketplaceRequestSource = CustomMarketplaceRequestSource.PRIVATE_BOT

    @field_validator("route_notes", "special_conditions")
    @classmethod
    def strip_opt(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def date_range_ok(self) -> BotCustomRequestCreate:
        end = self.travel_date_end or self.travel_date_start
        if end < self.travel_date_start:
            raise ValueError("travel_date_end must not be before travel_date_start.")
        return self


class OperationalActionFocusRead(StrEnum):
    """V2: coarse ops bucket — derived from existing request + bridge rows only."""

    TERMINAL = "terminal"
    AWAITING_SUPPLIER_PROPOSALS = "awaiting_supplier_proposals"
    INTERNAL_REVIEW_OR_RESOLUTION = "internal_review_or_resolution"
    BRIDGE_SETUP_OR_VALIDATION = "bridge_setup_or_validation"
    MONITOR_CUSTOMER_CONTINUATION = "monitor_customer_continuation"
    RECONCILE_CLOSED_BRIDGE = "reconcile_closed_bridge"


class OperationalSelectionLinkRead(StrEnum):
    """V3: how commercial selection relates to the request record (read-side)."""

    PRE_COMMERCIAL_DECISION = "pre_commercial_decision"
    SELECTED_RESPONSE_ON_FILE = "selected_response_on_file"
    SELECTION_DATA_INCOMPLETE = "selection_data_incomplete"
    CLOSED_RECORD = "closed_record"


class OperationalCustomerPathVisibilityRead(StrEnum):
    """V3: conservative customer-continuation visibility from ops perspective — not payment truth."""

    NOT_YET_APPLICABLE = "not_yet_applicable"
    NO_CUSTOMER_PATH_LINKED = "no_customer_path_linked"
    BRIDGE_PREP_ONLY = "bridge_prep_only"
    CUSTOMER_CONTINUATION_MAY_EXIST = "customer_continuation_may_exist"
    BRIDGE_NOT_ACTIVE = "bridge_not_active"
    TERMINAL_NO_FORWARD_PATH = "terminal_no_forward_path"


class OperationalFollowThroughPostureRead(StrEnum):
    """V4: where the case sits relative to real customer follow-through (RFQ/bridge snapshot only)."""

    TERMINAL_CLOSED = "terminal_closed"
    PRE_CUSTOMER_EXECUTION = "pre_customer_execution"
    SELECTION_DATA_GAP = "selection_data_gap"
    COMMERCIAL_WITHOUT_BRIDGE = "commercial_without_bridge"
    BRIDGE_AWAITING_CLEARANCE = "bridge_awaiting_clearance"
    PATH_MAY_EXIST_NO_PROGRESSION_EVIDENCE_HERE = "path_may_exist_no_progression_evidence_here"
    NOTIFY_MILESTONE_NO_COMPLETION_EVIDENCE = "notify_milestone_no_completion_evidence"
    BRIDGE_INACTIVE_STALLED = "bridge_inactive_stalled"


class OperationalCustomerProgressionEvidenceRead(StrEnum):
    """V4: what this API view can say about customer movement — not Layer A booking/payment truth."""

    NOT_APPLICABLE = "not_applicable"
    NO_CUSTOMER_PATH_VISIBLE = "no_customer_path_visible"
    NO_BOOKING_OR_PAYMENT_EVIDENCE_IN_THIS_VIEW = "no_booking_or_payment_evidence_in_this_view"
    NOTIFICATION_MILESTONE_ONLY = "notification_milestone_only"
    TERMINAL_NO_FURTHER_EVIDENCE_EXPECTED = "terminal_no_further_evidence_expected"


class CustomMarketplaceRequestOperationalListHintsRead(BaseModel):
    """V1–V4: admin/ops scan + handling + action + transition + light follow-through hint — not for customers."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_stage_label: str
    is_terminal: bool
    scan_summary_line: str
    proposed_supplier_response_count: int
    has_selected_supplier_response: bool
    handling_hint: str
    action_focus: OperationalActionFocusRead
    needs_internal_ops_attention: bool
    primary_action_hint: str
    transition_stage_one_liner: str
    follow_through_one_liner: str


class CustomMarketplaceRequestOperationalDetailHintsRead(CustomMarketplaceRequestOperationalListHintsRead):
    """V1–V4: detail adds bridge, transition, and follow-through interpretation (read-side only)."""

    model_config = ConfigDict(extra="forbid")

    booking_bridge_present: bool
    booking_bridge_operational_label: str | None = None
    continuation_summary: str
    bridge_continuation_interpretation: str = ""
    selection_link_state: OperationalSelectionLinkRead
    customer_path_visibility: OperationalCustomerPathVisibilityRead
    transition_chain_summary: str
    follow_through_posture: OperationalFollowThroughPostureRead
    customer_progression_evidence: OperationalCustomerProgressionEvidenceRead
    follow_through_summary: str


class SupplierPortalResponseWorkflowHintsRead(BaseModel):
    """X2: supplier’s own response context — readable state, editability, next step (no rule changes)."""

    model_config = ConfigDict(extra="forbid")

    your_response_state: Literal[
        "none_yet",
        "proposal_on_file",
        "decline_on_file",
        "proposal_was_selected",
        "decline_or_other_read_only",
    ]
    response_presence_one_liner: str
    response_kind_explained: str
    editability_one_liner: str
    selection_meaning_for_supplier: str
    what_happens_next: str


class SupplierPortalRequestHintsRead(BaseModel):
    """X1 scan/action + X2 response-workflow clarity — supplier-safe; not admin operational copy (V1–V4)."""

    model_config = ConfigDict(extra="forbid")

    request_summary_line: str = Field(description="Type, dates, group, route excerpt for quick scanning.")
    supplier_visible_headline: str = Field(description="Short headline for list/detail — actionability-focused.")
    customer_need_summary: str = Field(
        description="Plain description of what the customer asked for (from request fields only).",
    )
    supplier_has_responded: bool
    supplier_last_response_kind: Literal["proposed", "declined"] | None = None
    your_response_was_selected: bool = False
    can_submit_or_update_response: bool
    portal_action_state: Literal[
        "open_actionable_no_response_yet",
        "open_actionable_has_response",
        "under_review_actionable",
        "read_only_selection_recorded",
        "read_only_closed",
    ]
    portal_action_state_label: str
    portal_action_state_detail: str
    response_workflow: SupplierPortalResponseWorkflowHintsRead


class CustomMarketplaceRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    customer_telegram_user_id: int | None = Field(
        default=None,
        description="Admin/ops read-side customer Telegram id; None outside admin-populated surfaces.",
    )
    customer_summary: AdminCustomerSummary | None = Field(
        default=None,
        description="Admin/ops read-side customer label; None outside admin-populated surfaces.",
    )
    assigned_operator_id: int | None = Field(
        default=None,
        description="Internal users.id of the assigned operator; admin/ops only when populated.",
    )
    assigned_by_user_id: int | None = Field(
        default=None,
        description="Internal users.id of the actor who last set assignment; admin/ops only.",
    )
    assigned_at: datetime | None = Field(
        default=None,
        description="When the request was last assigned; admin/ops only.",
    )
    operator_summary: AdminCustomerSummary | None = Field(
        default=None,
        description="Label for assigned operator (User-backed); admin/ops only.",
    )
    assigned_operator_telegram_user_id: int | None = Field(
        default=None,
        description="Telegram id of assigned operator; admin/ops only (for client-side match).",
    )
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None
    route_notes: str
    group_size: int | None
    special_conditions: str | None
    source_channel: CustomMarketplaceRequestSource
    status: CustomMarketplaceRequestStatus
    admin_intervention_note: str | None
    operator_workflow_intent: OperatorWorkflowIntent | None = Field(
        default=None,
        description="Y37.4: machine-readable operator next-step intent; admin/ops only.",
    )
    operator_workflow_intent_set_at: datetime | None = Field(
        default=None,
        description="When the operator set workflow intent; admin/ops only.",
    )
    operator_workflow_intent_set_by_user_id: int | None = Field(
        default=None,
        description="Internal users.id of the actor who set intent; admin/ops only.",
    )
    selected_supplier_response_id: int | None = None
    commercial_resolution_kind: CommercialResolutionKind | None = None
    created_at: datetime
    updated_at: datetime
    operational_hints: CustomMarketplaceRequestOperationalListHintsRead | None = None
    supplier_portal_hints: SupplierPortalRequestHintsRead | None = Field(
        default=None,
        description="X1/X2: supplier portal list/detail only — request scan + response workflow clarity (supplier-safe).",
    )


class CustomMarketplaceRequestListRead(BaseModel):
    items: list[CustomMarketplaceRequestRead]
    total_returned: int


class SupplierCustomRequestResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    supplier_id: int
    supplier_code: str | None = None
    supplier_display_name: str | None = None
    response_kind: SupplierCustomRequestResponseKind
    supplier_message: str | None
    quoted_price: Decimal | None
    quoted_currency: str | None
    supplier_declared_sales_mode: TourSalesMode | None = None
    supplier_declared_payment_mode: SupplierOfferPaymentMode | None = None
    is_selected: bool = False
    created_at: datetime
    updated_at: datetime


class CustomRequestBookingBridgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    selected_supplier_response_id: int
    user_id: int
    tour_id: int | None
    bridge_status: CustomRequestBookingBridgeStatus
    admin_note: str | None
    created_at: datetime
    updated_at: datetime


class CustomMarketplaceRequestDetailRead(BaseModel):
    request: CustomMarketplaceRequestRead
    responses: list[SupplierCustomRequestResponseRead]
    customer_telegram_user_id: int | None = None
    booking_bridge: CustomRequestBookingBridgeRead | None = None
    effective_execution_policy: EffectiveCommercialExecutionPolicyRead | None = None
    operational_hints: CustomMarketplaceRequestOperationalDetailHintsRead | None = None
    prepared_customer_lifecycle_message: AdminPreparedCustomRequestLifecycleMessageRead | None = Field(
        default=None,
        description="W3: W1-prepared Mode 3 copy for internal/manual use — not sent, not outbox, not receipt proof.",
    )


class AdminCustomRequestBookingBridgeCreate(BaseModel):
    """Track 5b.1: admin explicitly creates execution intent — no Layer A side effects."""

    model_config = ConfigDict(extra="forbid")

    tour_id: int | None = Field(default=None, gt=0)
    admin_note: str | None = Field(default=None, max_length=8000)

    @field_validator("admin_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminCustomRequestBookingBridgePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tour_id: int | None = Field(default=None, gt=0)
    admin_note: str | None = Field(default=None, max_length=8000)

    @field_validator("admin_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def at_least_one(self) -> AdminCustomRequestBookingBridgePatch:
        if self.tour_id is None and self.admin_note is None:
            raise ValueError("Provide tour_id and/or admin_note.")
        return self


class AdminCustomRequestBookingBridgeClose(BaseModel):
    """Track 5e: close the active bridge only — no Layer A side effects."""

    model_config = ConfigDict(extra="forbid")

    terminal_status: Literal["superseded", "cancelled"]
    admin_note: str | None = Field(default=None, max_length=8000)

    @field_validator("admin_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class AdminCustomRequestBookingBridgeReplace(AdminCustomRequestBookingBridgeCreate):
    """Track 5e: supersede active bridge (if any) and create a new bridge row in one transaction."""

    supersede_note: str | None = Field(default=None, max_length=8000)

    @field_validator("supersede_note")
    @classmethod
    def strip_supersede_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class SupplierCustomRequestResponseUpsert(BaseModel):
    response_kind: SupplierCustomRequestResponseKind
    supplier_message: str | None = Field(default=None, max_length=8000)
    quoted_price: Decimal | None = Field(default=None, ge=0)
    quoted_currency: str | None = Field(default=None, max_length=8)
    supplier_declared_sales_mode: TourSalesMode | None = None
    supplier_declared_payment_mode: SupplierOfferPaymentMode | None = None

    @field_validator("supplier_message", "quoted_currency")
    @classmethod
    def strip_fields(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def proposed_rules(self) -> SupplierCustomRequestResponseUpsert:
        if self.response_kind == SupplierCustomRequestResponseKind.DECLINED:
            if self.supplier_declared_sales_mode is not None or self.supplier_declared_payment_mode is not None:
                raise ValueError("Declined responses must not set supplier_declared sales/payment fields.")
            return self
        if self.response_kind == SupplierCustomRequestResponseKind.PROPOSED:
            if not (self.supplier_message or "").strip():
                raise ValueError("supplier_message is required when response_kind is proposed.")
            if self.quoted_price is not None and not (self.quoted_currency or "").strip():
                raise ValueError("quoted_currency is required when quoted_price is set.")
            if self.supplier_declared_sales_mode is None or self.supplier_declared_payment_mode is None:
                raise ValueError(
                    "supplier_declared_sales_mode and supplier_declared_payment_mode are required when proposed.",
                )
            validate_supplier_declared_rfq_commercial_pair(
                sales_mode=self.supplier_declared_sales_mode,
                payment_mode=self.supplier_declared_payment_mode,
            )
        return self


class AdminOperatorDecisionApply(BaseModel):
    """Y37.4: first slice — one decision value only (extend enum + body in later tracks)."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["need_manual_followup"] = Field(
        description="V1: only need_manual_followup (internal follow-up, no automated supplier/bridge/booking).",
    )


class AdminCustomRequestPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    admin_intervention_note: str | None = Field(default=None, max_length=8000)
    status: CustomMarketplaceRequestStatus | None = None

    @field_validator("admin_intervention_note")
    @classmethod
    def strip_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @model_validator(mode="after")
    def at_least_one(self) -> AdminCustomRequestPatch:
        if self.admin_intervention_note is None and self.status is None:
            raise ValueError("Provide admin_intervention_note and/or status.")
        return self

    @model_validator(mode="after")
    def block_commercial_resolution_via_patch(self) -> AdminCustomRequestPatch:
        blocked = {
            CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
            CustomMarketplaceRequestStatus.CLOSED_ASSISTED,
            CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
            CustomMarketplaceRequestStatus.FULFILLED,
        }
        if self.status is not None and self.status in blocked:
            raise ValueError("Use POST /admin/custom-requests/{id}/resolution for commercial resolution statuses.")
        return self


class AdminCustomRequestResolutionApply(BaseModel):
    """Track 5a: record commercial resolution without creating orders or payments."""

    model_config = ConfigDict(extra="forbid")

    status: CustomMarketplaceRequestStatus
    commercial_resolution_kind: CommercialResolutionKind | None = None
    selected_supplier_response_id: int | None = None
    admin_intervention_note: str | None = Field(default=None, max_length=8000)

    @field_validator("admin_intervention_note")
    @classmethod
    def strip_resolution_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class MiniAppCustomRequestCustomerSummaryRead(BaseModel):
    id: int
    status: CustomMarketplaceRequestStatus
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None = None
    created_at: datetime
    group_size: int | None = None
    route_notes_preview: str | None = None
    customer_visible_summary: str
    activity_preview_title: str | None = None


class MiniAppCustomRequestCustomerListRead(BaseModel):
    items: list[MiniAppCustomRequestCustomerSummaryRead]
    total_returned: int


class MiniAppSelectedOfferSummaryRead(BaseModel):
    """Track 5f v1: read-only snippet for admin-selected proposal only — no supplier identity."""

    quoted_price: Decimal | None = None
    quoted_currency: str | None = None
    supplier_message_excerpt: str | None = Field(default=None, max_length=400)
    declared_sales_mode: str | None = None
    declared_payment_mode: str | None = None


class MiniAppCustomRequestCustomerDetailRead(BaseModel):
    id: int
    status: CustomMarketplaceRequestStatus
    created_at: datetime
    route_notes: str = Field(
        default="",
        description="U3: full route/notes text the customer submitted (same source as intake; for IA section).",
    )
    customer_visible_summary: str
    commercial_mode: CustomerCommercialMode = Field(
        default=CustomerCommercialMode.CUSTOM_BUS_RENTAL_REQUEST,
        description="Track 5g.1: RFQ / custom marketplace request (Mode 3).",
    )
    request_type: CustomMarketplaceRequestType
    travel_date_start: date
    travel_date_end: date | None
    group_size: int | None = None
    route_notes_preview: str | None = None
    latest_booking_bridge_status: CustomRequestBookingBridgeStatus | None = None
    latest_booking_bridge_tour_code: str | None = None
    proposed_response_count: int = 0
    offers_received_hint: str = ""
    selected_offer_summary: MiniAppSelectedOfferSummaryRead | None = None
    activity_preview: MiniAppCustomRequestActivityPreviewRead | None = None


class MiniAppCustomRequestCreatedRead(BaseModel):
    id: int
    status: CustomMarketplaceRequestStatus
