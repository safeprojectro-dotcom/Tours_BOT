"""Effective commercial execution policy for RFQ-linked tours (Track 5b.3a).

Composes TourSalesModePolicyService (Layer A mechanics), supplier-declared RFQ response
policy, and Track 5a resolution signals. Does not create payments or reservations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.enums import (
    CommercialResolutionKind,
    CustomMarketplaceRequestStatus,
    SupplierCustomRequestResponseKind,
    SupplierOfferPaymentMode,
    TourSalesMode,
)
from app.schemas.effective_commercial_execution_policy import EffectiveCommercialExecutionPolicyRead
from app.services.tour_sales_mode_policy import TourSalesModePolicyService

if TYPE_CHECKING:
    from app.models.custom_marketplace_request import CustomMarketplaceRequest, SupplierCustomRequestResponse
    from app.models.tour import Tour


def validate_supplier_declared_rfq_commercial_pair(
    *,
    sales_mode: TourSalesMode,
    payment_mode: SupplierOfferPaymentMode,
) -> None:
    """Conservative validation on supplier response upsert (proposed only)."""
    if sales_mode is TourSalesMode.FULL_BUS and payment_mode is SupplierOfferPaymentMode.PLATFORM_CHECKOUT:
        raise ValueError(
            "full_bus supplier intent cannot be combined with platform_checkout (unsupported self-serve checkout).",
        )
    if sales_mode is TourSalesMode.PER_SEAT:
        return
    if sales_mode is TourSalesMode.FULL_BUS and payment_mode is SupplierOfferPaymentMode.ASSISTED_CLOSURE:
        return
    raise ValueError(f"Unsupported supplier_declared combination: {sales_mode!r} + {payment_mode!r}.")


class EffectiveCommercialExecutionPolicyService:
    """Single resolver for RFQ bridge execution / payment gating read models."""

    @staticmethod
    def resolve(
        *,
        tour: Tour,
        request: CustomMarketplaceRequest,
        response: SupplierCustomRequestResponse,
    ) -> EffectiveCommercialExecutionPolicyRead:
        tour_policy = TourSalesModePolicyService.policy_for_tour(tour)

        external_only = request.status == CustomMarketplaceRequestStatus.CLOSED_EXTERNAL or (
            request.commercial_resolution_kind == CommercialResolutionKind.EXTERNAL_RECORD
        )

        incomplete = (
            response.response_kind == SupplierCustomRequestResponseKind.PROPOSED
            and (
                response.supplier_declared_sales_mode is None
                or response.supplier_declared_payment_mode is None
            )
        )

        supplier_platform_per_seat_intent = (
            not incomplete
            and response.response_kind == SupplierCustomRequestResponseKind.PROPOSED
            and response.supplier_declared_sales_mode == TourSalesMode.PER_SEAT
            and response.supplier_declared_payment_mode == SupplierOfferPaymentMode.PLATFORM_CHECKOUT
        )

        self_service_hold_allowed = (
            not external_only
            and not incomplete
            and supplier_platform_per_seat_intent
            and tour_policy.per_seat_self_service_allowed
        )
        self_service_preparation_allowed = self_service_hold_allowed

        platform_checkout_allowed = (
            not external_only
            and not incomplete
            and supplier_platform_per_seat_intent
            and tour_policy.per_seat_self_service_allowed
        )

        assisted_only = (not external_only) and (not self_service_hold_allowed)

        blocked_code: str | None = None
        blocked_reason: str | None = None
        customer_blocked_code: str | None = None

        if not self_service_hold_allowed:
            if external_only:
                blocked_code = "external_record"
                blocked_reason = "Request was closed as external / off-platform record."
                customer_blocked_code = "handled_externally"
            elif incomplete:
                blocked_code = "supplier_policy_incomplete"
                blocked_reason = "Proposed supplier response is missing declared commercial policy fields."
                customer_blocked_code = "supplier_policy_incomplete"
            elif not tour_policy.per_seat_self_service_allowed:
                blocked_code = "tour_sales_mode_blocks_self_service"
                blocked_reason = "Tour sales mode does not allow per-seat self-service execution."
                customer_blocked_code = "operator_assistance_required"
            elif not supplier_platform_per_seat_intent:
                blocked_code = "supplier_commercial_intent_blocks_self_service"
                blocked_reason = (
                    "Supplier declared assisted closure, full-bus charter intent, or non-platform handling."
                )
                customer_blocked_code = "operator_assistance_required"
            else:
                blocked_code = "execution_not_available"
                blocked_reason = "Self-service execution is not available for this RFQ context."
                customer_blocked_code = "operator_assistance_required"

        return EffectiveCommercialExecutionPolicyRead(
            self_service_preparation_allowed=self_service_preparation_allowed,
            self_service_hold_allowed=self_service_hold_allowed,
            platform_checkout_allowed=platform_checkout_allowed,
            assisted_only=assisted_only,
            external_only=external_only,
            blocked_code=blocked_code,
            blocked_reason=blocked_reason,
            customer_blocked_code=customer_blocked_code,
        )
