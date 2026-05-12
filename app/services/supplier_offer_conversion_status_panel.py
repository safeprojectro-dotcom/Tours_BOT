"""C2B11A — read-only Admin/OPS conversion status panel (derived from review-package inputs only)."""

from __future__ import annotations

from app.models.enums import SupplierOfferLifecycle, TourStatus
from app.schemas.mini_app import MiniAppSupplierOfferActionabilityState
from app.schemas.supplier_admin import (
    AdminSupplierOfferBridgeReadinessRead,
    AdminSupplierOfferConversionClosureRead,
    AdminSupplierOfferConversionStatusPanelLayerRead,
    AdminSupplierOfferConversionStatusPanelRead,
    AdminSupplierOfferExecutionLinksReviewRead,
    AdminSupplierOfferLinkedTourCatalogRead,
    AdminSupplierOfferMiniAppConversionPreviewRead,
    AdminSupplierOfferOperatorWorkflowRead,
    AdminSupplierOfferRead,
    AdminSupplierOfferShowcasePreviewRead,
)
from app.services.mini_app_supplier_offer_landing import SupplierOfferConversionPreviewForAdmin


def _truncate_detail(raw: str | None, *, max_len: int = 160) -> str | None:
    if raw is None:
        return None
    s = raw.strip().replace("\n", " ")
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def _showcase_row(
    *,
    offer: AdminSupplierOfferRead,
    showcase: AdminSupplierOfferShowcasePreviewRead,
    operator_workflow: AdminSupplierOfferOperatorWorkflowRead,
) -> AdminSupplierOfferConversionStatusPanelLayerRead:
    lc = offer.lifecycle_status
    if lc is SupplierOfferLifecycle.PUBLISHED:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="published",
            summary="Showcase: published (offer lifecycle is published).",
        )

    pub_act = next((a for a in operator_workflow.actions if a.code == "publish_showcase_channel"), None)

    if lc is SupplierOfferLifecycle.APPROVED:
        if not showcase.can_publish_now:
            return AdminSupplierOfferConversionStatusPanelLayerRead(
                status="blocked",
                summary="Showcase: blocked — Telegram channel or bot token not configured for publish.",
            )
        if pub_act is not None and not pub_act.enabled:
            return AdminSupplierOfferConversionStatusPanelLayerRead(
                status="blocked",
                summary="Showcase: blocked — packaging, moderation, preview, or cover media gate.",
                detail=_truncate_detail(pub_act.disabled_reason),
            )
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="not_published",
            summary="Showcase: approved but not posted to the channel yet.",
        )

    if pub_act is not None and not pub_act.enabled and lc is not SupplierOfferLifecycle.REJECTED:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="not_published",
            summary="Showcase: not published — complete earlier gates before channel publish.",
            detail=_truncate_detail(pub_act.disabled_reason),
        )

    return AdminSupplierOfferConversionStatusPanelLayerRead(
        status="not_published",
        summary="Showcase: not published yet.",
    )


def _bridge_row(
    *,
    closure: AdminSupplierOfferConversionClosureRead,
    bridge_readiness: AdminSupplierOfferBridgeReadinessRead,
) -> AdminSupplierOfferConversionStatusPanelLayerRead:
    if closure.has_tour_bridge:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="linked",
            summary="Tour bridge: linked (materialized tour exists for this offer).",
        )
    if not bridge_readiness.can_attempt_bridge and bridge_readiness.blocking_codes:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="missing",
            summary="Tour bridge: missing — prerequisites for materialization not met.",
            detail=_truncate_detail(", ".join(bridge_readiness.blocking_codes[:6])),
        )
    return AdminSupplierOfferConversionStatusPanelLayerRead(
        status="missing",
        summary="Tour bridge: missing — create/link a tour for this offer.",
    )


def _catalog_row(
    *,
    closure: AdminSupplierOfferConversionClosureRead,
    linked: AdminSupplierOfferLinkedTourCatalogRead | None,
) -> AdminSupplierOfferConversionStatusPanelLayerRead:
    if linked is None:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="not_listed",
            summary="Catalog: not listed — no bridged tour to activate for sale.",
        )
    if linked.b8_same_offer_date_conflict or linked.catalog_activation_missing_fields:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="blocked",
            summary="Catalog: blocked — activation guards or missing tour fields.",
            detail=_truncate_detail(
                "B8 conflict" if linked.b8_same_offer_date_conflict else ", ".join(linked.catalog_activation_missing_fields[:8]),
            ),
        )
    if linked.catalog_listed_for_mini_app or linked.tour_status == TourStatus.OPEN_FOR_SALE.value:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="listed_for_sale",
            summary="Catalog: listed for sale (open for sale in app catalog semantics).",
        )
    if linked.can_activate_for_catalog:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="not_listed",
            summary="Catalog: not listed — tour exists but is not marked for sale yet.",
        )
    return AdminSupplierOfferConversionStatusPanelLayerRead(
        status="not_listed",
        summary="Catalog: not listed for this bridged tour.",
    )


def _booking_link_row(
    *,
    offer: AdminSupplierOfferRead,
    exec_review: AdminSupplierOfferExecutionLinksReviewRead,
    linked: AdminSupplierOfferLinkedTourCatalogRead | None,
) -> AdminSupplierOfferConversionStatusPanelLayerRead:
    active = exec_review.active_link
    if active is not None and linked is not None and active.tour_id != linked.tour_id:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="stale",
            summary="Booking link: stale — active link targets a different tour than the current bridge.",
            detail=f"link tour_id={active.tour_id}, bridge tour_id={linked.tour_id}",
        )
    if active is not None:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="active",
            summary="Booking link: active — supplier offer maps to a tour for deep routing.",
        )
    if offer.lifecycle_status is not SupplierOfferLifecycle.PUBLISHED:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="missing",
            summary=(
                "Booking link: missing — create an active execution link after the tour is "
                "listed for sale and before channel publish."
            ),
            detail=_truncate_detail(exec_review.execution_link_precheck_note),
        )
    return AdminSupplierOfferConversionStatusPanelLayerRead(
        status="missing",
        summary=(
            "Booking link: missing — create an active execution link for the exact Mini App tour "
            "(channel publish requires it)."
        ),
        detail=_truncate_detail(exec_review.execution_link_precheck_note),
    )


def _customer_action_row(
    *,
    conv: SupplierOfferConversionPreviewForAdmin,
    mini_schema: AdminSupplierOfferMiniAppConversionPreviewRead,
    closure: AdminSupplierOfferConversionClosureRead,
) -> AdminSupplierOfferConversionStatusPanelLayerRead:
    if not conv.applicable or conv.actionability_state is None:
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="not_bookable_yet",
            summary="Customer action: not bookable from published-offer flow yet (offer not published or landing not applicable).",
        )

    st = conv.actionability_state
    if st is MiniAppSupplierOfferActionabilityState.BOOKABLE:
        if closure.bot_deeplink_routes_to_tour and closure.has_active_execution_link:
            return AdminSupplierOfferConversionStatusPanelLayerRead(
                status="open_exact_mini_app_tour",
                summary="Customer action: open exact Mini App tour — booking path available subject to live seats and Layer A.",
                detail=f"tour_code={mini_schema.linked_tour_code}" if mini_schema.linked_tour_code else None,
            )
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="not_bookable_yet",
            summary="Customer action: Mini App shows bookable state; bot deep link or landing may still need configuration.",
            detail=_truncate_detail(closure.next_missing_step),
        )

    if st in (
        MiniAppSupplierOfferActionabilityState.ASSISTED_ONLY,
        MiniAppSupplierOfferActionabilityState.SOLD_OUT,
        MiniAppSupplierOfferActionabilityState.UNAVAILABLE,
    ):
        return AdminSupplierOfferConversionStatusPanelLayerRead(
            status="assisted_fallback",
            summary="Customer action: assisted or browse — online self-serve booking not available for this snapshot.",
            detail=st.value,
        )

    return AdminSupplierOfferConversionStatusPanelLayerRead(
        status="not_bookable_yet",
        summary="Customer action: view-only or wait — catalog/visibility rules prevent self-serve booking yet.",
        detail=st.value,
    )


def build_conversion_status_panel(
    *,
    offer: AdminSupplierOfferRead,
    showcase: AdminSupplierOfferShowcasePreviewRead,
    bridge_readiness: AdminSupplierOfferBridgeReadinessRead,
    linked_tour_catalog: AdminSupplierOfferLinkedTourCatalogRead | None,
    execution_links_review: AdminSupplierOfferExecutionLinksReviewRead,
    mini_app_conversion_preview: AdminSupplierOfferMiniAppConversionPreviewRead,
    conversion_closure: AdminSupplierOfferConversionClosureRead,
    operator_workflow: AdminSupplierOfferOperatorWorkflowRead,
    conversion_preview: SupplierOfferConversionPreviewForAdmin,
) -> AdminSupplierOfferConversionStatusPanelRead:
    """Build the five-row panel using only inputs already computed for ``review_package``."""

    return AdminSupplierOfferConversionStatusPanelRead(
        showcase=_showcase_row(offer=offer, showcase=showcase, operator_workflow=operator_workflow),
        tour_bridge=_bridge_row(closure=conversion_closure, bridge_readiness=bridge_readiness),
        catalog=_catalog_row(closure=conversion_closure, linked=linked_tour_catalog),
        booking_link=_booking_link_row(offer=offer, exec_review=execution_links_review, linked=linked_tour_catalog),
        customer_action=_customer_action_row(
            conv=conversion_preview,
            mini_schema=mini_app_conversion_preview,
            closure=conversion_closure,
        ),
    )


__all__ = ["build_conversion_status_panel"]
