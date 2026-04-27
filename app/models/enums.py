from enum import StrEnum

from sqlalchemy import Enum as SQLAlchemyEnum


class BookingStatus(StrEnum):
    NEW = "new"
    CUSTOMER_QUESTION = "customer_question"
    OPERATOR_QUESTION = "operator_question"
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    READY_FOR_DEPARTURE = "ready_for_departure"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PaymentStatus(StrEnum):
    UNPAID = "unpaid"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"


class CancellationStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_OPERATOR = "cancelled_by_operator"
    CANCELLED_NO_PAYMENT = "cancelled_no_payment"
    MOVED_TO_ANOTHER_DATE = "moved_to_another_date"
    MOVED_TO_ANOTHER_TOUR = "moved_to_another_tour"
    NO_SHOW = "no_show"
    DUPLICATE = "duplicate"


class TourStatus(StrEnum):
    DRAFT = "draft"
    OPEN_FOR_SALE = "open_for_sale"
    COLLECTING_GROUP = "collecting_group"
    GUARANTEED = "guaranteed"
    SALES_CLOSED = "sales_closed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class TourSalesMode(StrEnum):
    PER_SEAT = "per_seat"
    FULL_BUS = "full_bus"


class CustomerCommercialMode(StrEnum):
    """Track 5g read-side commercial journey — catalog per-seat, catalog full-bus, or RFQ (custom request)."""

    SUPPLIER_ROUTE_PER_SEAT = "supplier_route_per_seat"
    SUPPLIER_ROUTE_FULL_BUS = "supplier_route_full_bus"
    CUSTOM_BUS_RENTAL_REQUEST = "custom_bus_rental_request"


class SupplierServiceComposition(StrEnum):
    """Layer B: what the supplier bundles with transport (marketplace formation)."""

    TRANSPORT_ONLY = "transport_only"
    TRANSPORT_GUIDE = "transport_guide"
    TRANSPORT_WATER = "transport_water"
    TRANSPORT_GUIDE_WATER = "transport_guide_water"


class SupplierOfferPaymentMode(StrEnum):
    """Commercial handling intent for a supplier offer (narrow Track 2 — no new payment execution)."""

    PLATFORM_CHECKOUT = "platform_checkout"
    ASSISTED_CLOSURE = "assisted_closure"


class SupplierOfferLifecycle(StrEnum):
    """Supplier offer lifecycle: supplier steps + platform moderation + showcase (Track 3)."""

    DRAFT = "draft"
    READY_FOR_MODERATION = "ready_for_moderation"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class SupplierOfferPackagingStatus(StrEnum):
    """B2: AI / admin packaging sub-state (orthogonal to :class:`SupplierOfferLifecycle`). B5 adds review terminal states."""

    NONE = "none"
    PACKAGING_PENDING = "packaging_pending"
    PACKAGING_GENERATED = "packaging_generated"
    NEEDS_ADMIN_REVIEW = "needs_admin_review"
    APPROVED_FOR_PUBLISH = "approved_for_publish"
    PACKAGING_REJECTED = "packaging_rejected"
    CLARIFICATION_REQUESTED = "clarification_requested"


class SupplierOfferTourBridgeStatus(StrEnum):
    """B10: one active bridge per offer; superseded/cancelled for audit."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class SupplierOfferTourBridgeKind(StrEnum):
    """B10: whether admin created a new Tour or linked an existing one."""

    CREATED_NEW_TOUR = "created_new_tour"
    LINKED_EXISTING_TOUR = "linked_existing_tour"


class SupplierOfferMediaReviewStatus(StrEnum):
    """B7.1: cover visual review metadata (packaging_draft_json.media_review); not lifecycle or channel publish."""

    APPROVED_FOR_CARD = "approved_for_card"
    REJECTED_BAD_QUALITY = "rejected_bad_quality"
    REJECTED_IRRELEVANT = "rejected_irrelevant"
    REPLACEMENT_REQUESTED = "replacement_requested"
    FALLBACK_CARD_REQUIRED = "fallback_card_required"


class SupplierLegalEntityType(StrEnum):
    """Y2.1a: minimal legal identity categories for supplier onboarding approval."""

    COMPANY = "company"
    INDIVIDUAL_ENTREPRENEUR = "individual_entrepreneur"
    AUTHORIZED_CARRIER = "authorized_carrier"


class SupplierOnboardingStatus(StrEnum):
    """Y2.1 supplier Telegram onboarding review state (identity/access gate)."""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class CustomMarketplaceRequestType(StrEnum):
    """Layer C: structured custom trip / group RFQ categories (Track 4)."""

    GROUP_TRIP = "group_trip"
    CUSTOM_ROUTE = "custom_route"
    OTHER = "other"


class OperatorWorkflowIntent(StrEnum):
    """Y37.4/Y37.5: operator-only next-step intent on an RFQ — orthogonal to `CustomMarketplaceRequestStatus`."""

    NEED_MANUAL_FOLLOWUP = "need_manual_followup"
    NEED_SUPPLIER_OFFER = "need_supplier_offer"


class SupplierExecutionSourceEntryPoint(StrEnum):
    """Y39/Y41: how a supplier execution run was started (documentation enum; not Layer C)."""

    ADMIN_EXPLICIT = "admin_explicit"
    SCHEDULED_JOB = "scheduled_job"
    EXTERNAL_WEBHOOK = "external_webhook"
    OPERATOR_DO_ACTION = "operator_do_action"


class SupplierExecutionSourceEntityType(StrEnum):
    """Primary entity the execution run concerns (Y41) — keep minimal; extend in future tickets."""

    CUSTOM_MARKETPLACE_REQUEST = "custom_marketplace_request"


class SupplierExecutionRequestStatus(StrEnum):
    """Y41: lifecycle of a supplier_execution_requests row — not `CustomMarketplaceRequest.status` or live intent."""

    PENDING = "pending"
    VALIDATED = "validated"
    BLOCKED = "blocked"
    ATTEMPTED = "attempted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SupplierExecutionAttemptChannel(StrEnum):
    """Y41: channel for an attempt (placeholder until messaging exists)."""

    TELEGRAM = "telegram"
    EMAIL = "email"
    PARTNER_API = "partner_api"
    INTERNAL = "internal"
    NONE = "none"


class SupplierExecutionAttemptStatus(StrEnum):
    """Y41: per-attempt outcome."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class CustomMarketplaceRequestStatus(StrEnum):
    """Custom request lifecycle — separate from order/booking states (Track 4–5a)."""

    OPEN = "open"
    UNDER_REVIEW = "under_review"
    SUPPLIER_SELECTED = "supplier_selected"
    CLOSED_ASSISTED = "closed_assisted"
    CLOSED_EXTERNAL = "closed_external"
    CANCELLED = "cancelled"
    FULFILLED = "fulfilled"  # legacy DB value; migrated to closed_assisted in Track 5a migration


class CommercialResolutionKind(StrEnum):
    """How commercial closure was handled (Track 5a) — no payment execution."""

    ASSISTED_CLOSURE = "assisted_closure"
    EXTERNAL_RECORD = "external_record"


class CustomMarketplaceRequestSource(StrEnum):
    """Where the customer submitted the RFQ."""

    PRIVATE_BOT = "private_bot"
    MINI_APP = "mini_app"


class SupplierCustomRequestResponseKind(StrEnum):
    """Supplier stance on a marketplace request."""

    DECLINED = "declined"
    PROPOSED = "proposed"


class CustomRequestBookingBridgeStatus(StrEnum):
    """Layer C → Layer A execution intent (Track 5b.1) — not an order lifecycle."""

    PENDING_VALIDATION = "pending_validation"
    READY = "ready"
    LINKED_TOUR = "linked_tour"
    CUSTOMER_NOTIFIED = "customer_notified"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


def sqlalchemy_enum(enum_cls: type[StrEnum], *, name: str) -> SQLAlchemyEnum:
    return SQLAlchemyEnum(
        enum_cls,
        name=name,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
