"""Read-only operator workflow read-model for admin ``GET …/review-package`` (no mutations)."""

from __future__ import annotations

from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus
from app.schemas.supplier_admin import (
    AdminSupplierOfferAiPublicCopyReviewRead,
    AdminSupplierOfferBridgeReadinessRead,
    AdminSupplierOfferContentQualityReviewRead,
    AdminSupplierOfferConversionClosureRead,
    AdminSupplierOfferExecutionLinksReviewRead,
    AdminSupplierOfferLinkedTourCatalogRead,
    AdminSupplierOfferOperatorWorkflowActionRead,
    AdminSupplierOfferOperatorWorkflowRead,
    AdminSupplierOfferShowcasePreviewRead,
)

_DISPLAY_STATE_FROM_STEP: dict[str, str] = {
    "approve_packaging": "awaiting_packaging_approval",
    "address_moderation_rejection": "moderation_rejected",
    "complete_required_offer_fields_for_bridge": "offer_incomplete_for_bridge",
    "resolve_tour_bridge_prerequisites": "bridge_prerequisites_blocked",
    "create_tour_bridge": "ready_to_create_tour_bridge",
    "complete_linked_tour_for_catalog_activation": "linked_tour_incomplete_for_catalog",
    "resolve_catalog_activation_conflict": "catalog_activation_conflict",
    "activate_tour_for_catalog": "ready_to_activate_catalog",
    "moderation_approve": "awaiting_moderation_approval",
    "publish_showcase_channel": "ready_to_publish_showcase",
    "advance_offer_to_published_for_execution_link": "awaiting_publish_for_execution_link",
    "create_execution_link": "ready_to_create_execution_link",
    "ensure_linked_tour_materialized": "tour_bridge_missing",
    "ensure_customer_catalog_visibility_window": "catalog_visibility_pending",
    "ensure_supplier_offer_landing_resolution": "landing_resolution_pending",
    "ensure_bot_deep_link_mini_app_base_url": "bot_deeplink_configuration_pending",
}

_PRIMARY_ACTION_BY_STEP: dict[str, str] = {
    "approve_packaging": "approve_packaging_for_publish",
    "resolve_tour_bridge_prerequisites": "approve_packaging_for_publish",
    "create_tour_bridge": "create_tour_bridge",
    "complete_linked_tour_for_catalog_activation": "activate_tour_for_catalog",
    "resolve_catalog_activation_conflict": "activate_tour_for_catalog",
    "activate_tour_for_catalog": "activate_tour_for_catalog",
    "moderation_approve": "approve_offer_moderation",
    "publish_showcase_channel": "publish_showcase_channel",
    "advance_offer_to_published_for_execution_link": "publish_showcase_channel",
    "create_execution_link": "create_execution_link",
    "ensure_linked_tour_materialized": "create_tour_bridge",
    "ensure_customer_catalog_visibility_window": "activate_tour_for_catalog",
    "ensure_supplier_offer_landing_resolution": "create_execution_link",
    "ensure_bot_deep_link_mini_app_base_url": "review_package_refresh",
}

_PIPELINE_POST_CODES = (
    "generate_packaging_draft",
    "approve_packaging_for_publish",
    "approve_offer_moderation",
    "create_tour_bridge",
    "activate_tour_for_catalog",
    "publish_showcase_channel",
    "create_execution_link",
)


def _norm_packaging(st: SupplierOfferPackagingStatus | str) -> SupplierOfferPackagingStatus:
    if isinstance(st, SupplierOfferPackagingStatus):
        return st
    return SupplierOfferPackagingStatus(st)


def _norm_lifecycle(st: SupplierOfferLifecycle | str) -> SupplierOfferLifecycle:
    if isinstance(st, SupplierOfferLifecycle):
        return st
    return SupplierOfferLifecycle(st)


def _workflow_state(step: str | None) -> str:
    if step is None:
        return "conversion_complete"
    return _DISPLAY_STATE_FROM_STEP.get(step, step)


def _disabled_note(reasons: list[str]) -> str | None:
    if not reasons:
        return None
    return "; ".join(reasons[:5])


def build_operator_workflow(
    *,
    tour_id: int | None,
    packaging_status: SupplierOfferPackagingStatus | str,
    lifecycle_status: SupplierOfferLifecycle | str,
    closure: AdminSupplierOfferConversionClosureRead,
    bridge_readiness: AdminSupplierOfferBridgeReadinessRead,
    linked_tour_catalog: AdminSupplierOfferLinkedTourCatalogRead | None,
    execution_links_review: AdminSupplierOfferExecutionLinksReviewRead,
    showcase_preview: AdminSupplierOfferShowcasePreviewRead,
    ai_public_copy_review: AdminSupplierOfferAiPublicCopyReviewRead,
    content_quality_review: AdminSupplierOfferContentQualityReviewRead,
) -> AdminSupplierOfferOperatorWorkflowRead:
    """Derive read-only operator hints from existing review-package slices only.

    Does not perform HTTP calls or DB mutations — purely projects hints from inputs.
    """
    pk = _norm_packaging(packaging_status)
    lc = _norm_lifecycle(lifecycle_status)
    step = closure.next_missing_step
    state = _workflow_state(step)

    advisory_fact_lock = (
        ai_public_copy_review.ai_block_present and not ai_public_copy_review.fact_lock_passed
    )

    actions: list[AdminSupplierOfferOperatorWorkflowActionRead] = []

    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="review_package_refresh",
            label="Refresh review package",
            enabled=True,
            danger_level="safe_read",
            requires_confirmation=False,
            method="GET",
            endpoint="/admin/supplier-offers/{offer_id}/review-package",
            disabled_reason=None,
        ),
    )

    gen_enabled = pk is not SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH
    gen_dr: list[str] = []
    if pk is SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
        gen_dr.append("Packaging already approved for publish.")
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="generate_packaging_draft",
            label="Generate packaging draft",
            enabled=gen_enabled,
            danger_level="safe_mutation",
            requires_confirmation=False,
            method="POST",
            endpoint="/admin/supplier-offers/{offer_id}/packaging/generate",
            disabled_reason=_disabled_note(gen_dr),
        ),
    )

    appr_ok = pk in (
        SupplierOfferPackagingStatus.PACKAGING_GENERATED,
        SupplierOfferPackagingStatus.NEEDS_ADMIN_REVIEW,
    )
    appr_dr: list[str] = []
    if not appr_ok:
        if pk is SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
            appr_dr.append("Packaging already approved.")
        elif pk in (SupplierOfferPackagingStatus.PACKAGING_REJECTED, SupplierOfferPackagingStatus.NONE):
            appr_dr.append("Generate packaging before approval.")
        else:
            appr_dr.append(f"Cannot approve packaging from status {pk.value}.")
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="approve_packaging_for_publish",
            label="Approve packaging for publish",
            enabled=appr_ok,
            danger_level="safe_mutation",
            requires_confirmation=pk is SupplierOfferPackagingStatus.NEEDS_ADMIN_REVIEW,
            method="POST",
            endpoint="/admin/supplier-offers/{offer_id}/packaging/approve",
            disabled_reason=_disabled_note(appr_dr),
        ),
    )

    mod_ok = lc is SupplierOfferLifecycle.READY_FOR_MODERATION
    mod_dr: list[str] = []
    if lc is SupplierOfferLifecycle.DRAFT:
        mod_dr.append("Offer not submitted for moderation.")
    elif lc is SupplierOfferLifecycle.REJECTED:
        mod_dr.append("Moderation rejected — resolve before approval.")
    elif lc is SupplierOfferLifecycle.APPROVED:
        mod_dr.append("Already moderation-approved.")
    elif lc is SupplierOfferLifecycle.PUBLISHED:
        mod_dr.append("Already published.")
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="approve_offer_moderation",
            label="Approve offer for moderation lifecycle",
            enabled=mod_ok,
            danger_level="safe_mutation",
            requires_confirmation=False,
            method="POST",
            endpoint="/admin/supplier-offers/{offer_id}/moderation/approve",
            disabled_reason=_disabled_note(mod_dr),
        ),
    )

    bridge_dr = list(bridge_readiness.blocking_codes)
    if bridge_readiness.missing_fields:
        bridge_dr.append("Missing fields: " + ", ".join(bridge_readiness.missing_fields))
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="create_tour_bridge",
            label="Create or replay tour bridge",
            enabled=bridge_readiness.can_attempt_bridge,
            danger_level="safe_mutation",
            requires_confirmation=False,
            method="POST",
            endpoint="/admin/supplier-offers/{offer_id}/tour-bridge",
            disabled_reason=_disabled_note(bridge_dr),
        ),
    )

    act_tid = tour_id if tour_id is not None else (linked_tour_catalog.tour_id if linked_tour_catalog else None)
    act_ok = bool(linked_tour_catalog and linked_tour_catalog.can_activate_for_catalog and act_tid is not None)
    act_dr: list[str] = []
    if linked_tour_catalog is None:
        act_dr.append("No linked Tour — create tour bridge first.")
    elif linked_tour_catalog.b8_same_offer_date_conflict:
        act_dr.append("Catalog activation blocked by same-offer/date conflict (B8.3).")
    elif linked_tour_catalog.catalog_activation_missing_fields:
        act_dr.append(
            "Tour missing catalog activation fields: " + ", ".join(linked_tour_catalog.catalog_activation_missing_fields),
        )
    elif not linked_tour_catalog.can_activate_for_catalog:
        act_dr.append("Tour cannot be activated for catalog in current state.")
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="activate_tour_for_catalog",
            label="Activate Tour for Mini App catalog",
            enabled=act_ok,
            danger_level="conversion_enabling",
            requires_confirmation=True,
            method="POST",
            endpoint="/admin/tours/{tour_id}/activate-for-catalog",
            disabled_reason=_disabled_note(act_dr),
        ),
    )

    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="get_showcase_preview",
            label="Showcase preview (read)",
            enabled=True,
            danger_level="safe_read",
            requires_confirmation=False,
            method="GET",
            endpoint="/admin/supplier-offers/{offer_id}/showcase-preview",
            disabled_reason=None,
        ),
    )

    pub_ok = lc is SupplierOfferLifecycle.APPROVED and showcase_preview.can_publish_now
    pub_dr: list[str] = []
    if lc is not SupplierOfferLifecycle.APPROVED:
        pub_dr.append("Lifecycle must be moderation-approved before publish.")
    if not showcase_preview.can_publish_now:
        pub_dr.append("Showcase publish configuration or lifecycle blocks publish_now.")
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="publish_showcase_channel",
            label="Publish showcase to Telegram channel",
            enabled=pub_ok,
            danger_level="public_dangerous",
            requires_confirmation=True,
            method="POST",
            endpoint="/admin/supplier-offers/{offer_id}/publish",
            disabled_reason=_disabled_note(pub_dr),
        ),
    )

    el_ok = execution_links_review.can_create_execution_link
    el_dr: list[str] = []
    if not el_ok and execution_links_review.execution_link_precheck_note:
        el_dr.append(execution_links_review.execution_link_precheck_note)
    elif not el_ok:
        el_dr.append("Cannot create execution link in current state.")
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="create_execution_link",
            label="Create execution link",
            enabled=el_ok,
            danger_level="conversion_enabling",
            requires_confirmation=True,
            method="POST",
            endpoint="/admin/supplier-offers/{offer_id}/execution-link",
            disabled_reason=_disabled_note(el_dr),
        ),
    )

    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="verify_mini_app_catalog",
            label="Verify Mini App catalog listing (customer)",
            enabled=True,
            danger_level="safe_read",
            requires_confirmation=False,
            method="GET",
            endpoint="/mini-app/catalog",
            disabled_reason=None,
        ),
    )
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="verify_supplier_offer_landing",
            label="Verify supplier-offer landing (Mini App)",
            enabled=True,
            danger_level="safe_read",
            requires_confirmation=False,
            method="GET",
            endpoint="/mini-app/supplier-offers/{offer_id}",
            disabled_reason=None,
        ),
    )
    actions.append(
        AdminSupplierOfferOperatorWorkflowActionRead(
            code="verify_bot_deep_link",
            label="Verify bot deeplink routing (see conversion_closure.bot_deeplink_routes_to_tour)",
            enabled=True,
            danger_level="safe_read",
            requires_confirmation=False,
            method="GET",
            endpoint="/admin/supplier-offers/{offer_id}/review-package",
            disabled_reason=None,
        ),
    )

    primary_code: str | None = None
    if step is not None:
        wanted = _PRIMARY_ACTION_BY_STEP.get(step)
        if wanted is not None:
            cand = next((a for a in actions if a.code == wanted), None)
            if cand is not None and cand.enabled:
                primary_code = cand.code
        if primary_code is None:
            for code in _PIPELINE_POST_CODES:
                cand = next((a for a in actions if a.code == code), None)
                if cand is not None and cand.enabled:
                    primary_code = cand.code
                    break

    blocking_reasons: list[str] = []
    if lc is SupplierOfferLifecycle.REJECTED:
        blocking_reasons.append("Moderation rejected — resolve with supplier before advancing.")
    if bridge_readiness.blocking_codes:
        blocking_reasons.append("Tour bridge blocked: " + ", ".join(bridge_readiness.blocking_codes))
    if linked_tour_catalog is not None and linked_tour_catalog.b8_same_offer_date_conflict:
        blocking_reasons.append("Catalog activation conflict (duplicate active tour for offer/date).")

    ow_warnings: list[str] = []
    if advisory_fact_lock:
        ow_warnings.append("AI public copy fact lock requires attention (see ai_public_copy_review).")
    for w in content_quality_review.warnings:
        ow_warnings.append(f"[{w.code}] {w.message}")

    return AdminSupplierOfferOperatorWorkflowRead(
        state=state,
        primary_next_action=primary_code,
        actions=actions,
        blocking_reasons=blocking_reasons,
        warnings=ow_warnings,
    )


__all__ = ["build_operator_workflow"]
