"""Read-only admin aggregation for supplier offer review before bridge/catalog/showcase steps."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus, TourStatus
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from app.repositories.supplier import SupplierOfferRepository
from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository
from app.schemas.supplier_admin import (
    AdminSupplierOfferAiPublicCopyReviewRead,
    AdminSupplierOfferBridgeReadinessRead,
    AdminSupplierOfferContentQualityReviewRead,
    AdminSupplierOfferConversionClosureRead,
    AdminSupplierOfferCoverMediaQualityReviewRead,
    AdminSupplierOfferExecutionLinksReviewRead,
    AdminSupplierOfferLinkedTourCatalogRead,
    AdminSupplierOfferMiniAppConversionPreviewRead,
    AdminSupplierOfferRead,
    AdminSupplierOfferReviewPackageRead,
    AdminSupplierOfferShowcasePreviewRead,
    AdminSupplierOfferTourBridgeRead,
    SupplierOfferExecutionLinkRead,
)
from app.services.admin_tour_write import AdminTourWriteService, TourCatalogActivationPreview
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.mini_app_supplier_offer_landing import (
    MiniAppSupplierOfferLandingService,
    SupplierOfferConversionPreviewForAdmin,
)
from app.services.supplier_offer_ai_public_copy_fact_lock import evaluate_ai_public_copy_fact_lock
from app.services.supplier_offer_bot_start_routing import resolve_sup_offer_start_mini_app_routing
from app.services.supplier_offer_content_quality_review import evaluate_content_quality_review
from app.services.supplier_offer_cover_media_quality_review import evaluate_cover_media_quality_review
from app.services.supplier_offer_operator_workflow import build_operator_workflow
from app.services.supplier_offer_moderation_service import SupplierOfferModerationService
from app.services.supplier_offer_tour_bridge_service import (
    SupplierOfferBridgeMaterializationReadiness,
    SupplierOfferTourBridgeResult,
    SupplierOfferTourBridgeService,
)


class SupplierOfferReviewPackageNotFoundError(Exception):
    """No supplier offer row for id."""


def _merge_warnings(
    *,
    showcase: AdminSupplierOfferShowcasePreviewRead,
    bridge_blocking: list[str],
    bridge_missing: list[str],
    catalog: TourCatalogActivationPreview | None,
    ai_fact_lock: AdminSupplierOfferAiPublicCopyReviewRead | None = None,
    content_quality: AdminSupplierOfferContentQualityReviewRead | None = None,
    cover_media_quality: AdminSupplierOfferCoverMediaQualityReviewRead | None = None,
) -> list[str]:
    out: list[str] = []
    out.extend(showcase.warnings)
    if bridge_blocking:
        out.append(
            "Tour bridge prerequisites not met: " + ", ".join(bridge_blocking) + ". "
            "(Requires packaging approved_for_publish; lifecycle must not be rejected.)",
        )
    if bridge_missing:
        out.append("Offer missing fields for tour materialization: " + ", ".join(bridge_missing) + ".")
    if catalog and catalog.b8_same_offer_date_conflict:
        out.append(
            "Catalog activation may be blocked (B8.3): another open_for_sale tour exists for the same "
            "source supplier offer and departure.",
        )
    if ai_fact_lock is not None:
        out.extend(ai_fact_lock.warnings)
        for bi in ai_fact_lock.blocking_issues:
            out.append("AI fact lock: " + bi)
    if content_quality is not None:
        for w in content_quality.warnings:
            out.append(f"Content quality [{w.code}]: {w.message}")
    if cover_media_quality is not None:
        for w in cover_media_quality.warnings:
            out.append(f"Cover media [{w.code}]: {w.message}")
    return out


def _recommended_next_actions(
    *,
    offer: SupplierOffer,
    bridge_rd: SupplierOfferBridgeMaterializationReadiness,
    active_bridge: SupplierOfferTourBridgeResult | None,
    catalog: TourCatalogActivationPreview | None,
    has_active_execution_link: bool,
    lifecycle_published: bool,
    ai_fact_lock: AdminSupplierOfferAiPublicCopyReviewRead | None = None,
    content_quality: AdminSupplierOfferContentQualityReviewRead | None = None,
) -> list[str]:
    actions: list[str] = []
    if ai_fact_lock is not None and ai_fact_lock.ai_block_present and not ai_fact_lock.fact_lock_passed:
        actions.append("resolve_ai_public_copy_fact_lock")
    if content_quality is not None and content_quality.has_quality_warnings:
        actions.append("review_supplier_offer_content_quality")
    if offer.packaging_status is not SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
        actions.append("approve_packaging")
    if bridge_rd.missing_fields:
        actions.append("complete_required_offer_fields_for_bridge")
    if offer.lifecycle_status is SupplierOfferLifecycle.REJECTED:
        actions.append("address_moderation_rejection")
    if active_bridge is None and bridge_rd.can_attempt_bridge:
        actions.append("create_tour_bridge")
    if catalog is not None and catalog.can_activate_for_catalog:
        actions.append("activate_tour_for_catalog")
    if offer.lifecycle_status is SupplierOfferLifecycle.READY_FOR_MODERATION:
        actions.append("moderation_approve")
    if offer.lifecycle_status is SupplierOfferLifecycle.APPROVED:
        actions.append("publish_showcase_optional")
    if lifecycle_published and not has_active_execution_link:
        actions.append("create_execution_link")
    return actions[:12]


def _next_missing_conversion_step(
    *,
    offer: SupplierOffer,
    bridge_rd: SupplierOfferBridgeMaterializationReadiness,
    active_bridge: SupplierOfferTourBridgeResult | None,
    catalog: TourCatalogActivationPreview | None,
    lifecycle_pub: bool,
    can_create_exec: bool,
    tour_row: Tour | None,
    catalog_contains: bool,
    landing_ok: bool,
    bot_ok: bool,
) -> str | None:
    """Single suggested gate — explicit admin sequence; does not auto-trigger actions."""
    if offer.packaging_status is not SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
        return "approve_packaging"
    if offer.lifecycle_status is SupplierOfferLifecycle.REJECTED:
        return "address_moderation_rejection"
    if bridge_rd.missing_fields:
        return "complete_required_offer_fields_for_bridge"
    if active_bridge is None:
        if bridge_rd.can_attempt_bridge:
            return "create_tour_bridge"
        return "resolve_tour_bridge_prerequisites"
    if catalog is not None:
        if catalog.catalog_activation_missing_fields:
            return "complete_linked_tour_for_catalog_activation"
        if catalog.b8_same_offer_date_conflict:
            return "resolve_catalog_activation_conflict"
        if catalog.can_activate_for_catalog:
            return "activate_tour_for_catalog"
    if offer.lifecycle_status is SupplierOfferLifecycle.READY_FOR_MODERATION:
        return "moderation_approve"
    if offer.lifecycle_status is SupplierOfferLifecycle.APPROVED:
        return "publish_showcase_channel"
    if not lifecycle_pub:
        return "advance_offer_to_published_for_execution_link"
    if can_create_exec:
        return "create_execution_link"
    if tour_row is None:
        return "ensure_linked_tour_materialized"
    if tour_row.status is not TourStatus.OPEN_FOR_SALE:
        return "activate_tour_for_catalog"
    if not catalog_contains:
        return "ensure_customer_catalog_visibility_window"
    if not landing_ok:
        return "ensure_supplier_offer_landing_resolution"
    if not bot_ok:
        return "ensure_bot_deep_link_mini_app_base_url"
    return None


def _build_conversion_closure(
    *,
    offer: SupplierOffer,
    bridge_rd: SupplierOfferBridgeMaterializationReadiness,
    active_bridge: SupplierOfferTourBridgeResult | None,
    catalog: TourCatalogActivationPreview | None,
    active_exec: object | None,
    lifecycle_pub: bool,
    can_create_exec: bool,
    conv: SupplierOfferConversionPreviewForAdmin,
    tour_row: Tour | None,
    session: Session,
) -> AdminSupplierOfferConversionClosureRead:
    has_bridge = active_bridge is not None
    has_exec = active_exec is not None

    has_catalog_visible = (
        tour_row is not None and tour_row.status is TourStatus.OPEN_FOR_SALE
    )
    catalog_contains = False
    if tour_row is not None and tour_row.status is TourStatus.OPEN_FOR_SALE:
        catalog_contains = tour_is_customer_catalog_visible(
            departure_datetime=tour_row.departure_datetime,
            sales_deadline=tour_row.sales_deadline,
        )

    landing_ok = (
        conv.applicable
        and bool(conv.linked_tour_id)
        and bool((conv.linked_tour_code or "").strip())
    )

    mini_base = (get_settings().telegram_mini_app_url or "").strip()
    nav = resolve_sup_offer_start_mini_app_routing(session, offer=offer, mini_app_base_url=mini_base)
    bot_ok = nav.exact_tour_mini_app_url is not None

    next_step = _next_missing_conversion_step(
        offer=offer,
        bridge_rd=bridge_rd,
        active_bridge=active_bridge,
        catalog=catalog,
        lifecycle_pub=lifecycle_pub,
        can_create_exec=can_create_exec,
        tour_row=tour_row,
        catalog_contains=catalog_contains,
        landing_ok=landing_ok,
        bot_ok=bot_ok,
    )

    all_green = (
        has_bridge
        and has_catalog_visible
        and catalog_contains
        and has_exec
        and landing_ok
        and bot_ok
    )
    if all_green:
        next_step = None

    return AdminSupplierOfferConversionClosureRead(
        has_tour_bridge=has_bridge,
        has_catalog_visible_tour=has_catalog_visible,
        has_active_execution_link=has_exec,
        supplier_offer_landing_routes_to_tour=landing_ok,
        bot_deeplink_routes_to_tour=bot_ok,
        central_catalog_contains_tour=catalog_contains,
        next_missing_step=next_step,
    )


def _bridge_result_to_read(res: SupplierOfferTourBridgeResult) -> AdminSupplierOfferTourBridgeRead:
    return AdminSupplierOfferTourBridgeRead(
        id=res.id,
        supplier_offer_id=res.supplier_offer_id,
        tour_id=res.tour_id,
        bridge_status=res.bridge_status,
        bridge_kind=res.bridge_kind,
        tour_status=res.tour_status,
        created_at=res.created_at,
        idempotent_replay=res.idempotent_replay,
        warnings=res.warnings,
        notes=res.notes,
        source_packaging_status=res.source_packaging_status,
        source_lifecycle_status=res.source_lifecycle_status,
    )


def _catalog_preview_to_read(p: TourCatalogActivationPreview) -> AdminSupplierOfferLinkedTourCatalogRead:
    return AdminSupplierOfferLinkedTourCatalogRead(
        tour_id=p.tour_id,
        tour_code=p.tour_code,
        tour_status=p.tour_status,
        sales_mode=p.sales_mode,
        seats_available=p.seats_available,
        catalog_activation_missing_fields=p.catalog_activation_missing_fields,
        catalog_listed_for_mini_app=p.catalog_listed_for_mini_app,
        can_activate_for_catalog=p.can_activate_for_catalog,
        b8_same_offer_date_conflict=p.b8_same_offer_date_conflict,
    )


class SupplierOfferReviewPackageService:
    """Aggregates existing read-only checks without mutating lifecycle, tours, or Telegram."""

    def __init__(
        self,
        *,
        offers: SupplierOfferRepository | None = None,
        exec_links: SupplierOfferExecutionLinkRepository | None = None,
        bridge_svc: SupplierOfferTourBridgeService | None = None,
        moderation_svc: SupplierOfferModerationService | None = None,
        tour_write: AdminTourWriteService | None = None,
        landing_svc: MiniAppSupplierOfferLandingService | None = None,
    ) -> None:
        self._offers = offers or SupplierOfferRepository()
        self._exec_links = exec_links or SupplierOfferExecutionLinkRepository()
        self._bridge = bridge_svc or SupplierOfferTourBridgeService()
        self._moderation = moderation_svc or SupplierOfferModerationService()
        self._tour_write = tour_write or AdminTourWriteService()
        self._landing = landing_svc or MiniAppSupplierOfferLandingService()

    def review_package(self, session: Session, *, offer_id: int) -> AdminSupplierOfferReviewPackageRead:
        row = self._offers.get_any(session, offer_id=offer_id)
        if row is None:
            raise SupplierOfferReviewPackageNotFoundError

        offer_read = AdminSupplierOfferRead.model_validate(row, from_attributes=True)
        showcase = self._moderation.showcase_preview(session, offer_id=offer_id)

        bridge_rd = self._bridge.read_bridge_materialization_readiness(row)

        active_bridge_result = self._bridge.get_active_bridge(session, supplier_offer_id=offer_id)

        linked_catalog: AdminSupplierOfferLinkedTourCatalogRead | None = None
        catalog_preview: TourCatalogActivationPreview | None = None
        if active_bridge_result is not None:
            catalog_preview = self._tour_write.preview_catalog_activation_for_tour(
                session,
                tour_id=active_bridge_result.tour_id,
            )
            if catalog_preview is not None:
                linked_catalog = _catalog_preview_to_read(catalog_preview)

        all_links = self._exec_links.list_for_offer(session, supplier_offer_id=offer_id)
        active_exec = self._exec_links.get_active_for_offer(session, supplier_offer_id=offer_id, for_update=False)
        lifecycle_pub = row.lifecycle_status == SupplierOfferLifecycle.PUBLISHED

        exec_note: str | None = None
        can_create = False
        if not lifecycle_pub:
            exec_note = "Execution links can be created only when lifecycle_status is published."
        elif active_exec is not None:
            exec_note = "An active execution link already exists; replace or close it before creating another."
        else:
            can_create = True

        conv = self._landing.read_conversion_preview_for_admin_review(session, offer=row)
        mini_app = AdminSupplierOfferMiniAppConversionPreviewRead(
            applicable=conv.applicable,
            actionability_state=conv.actionability_state.value if conv.actionability_state is not None else None,
            has_execution_link=conv.has_execution_link if conv.applicable else None,
            linked_tour_id=conv.linked_tour_id if conv.applicable else None,
            linked_tour_code=conv.linked_tour_code if conv.applicable else None,
        )

        ai_public_copy_review = evaluate_ai_public_copy_fact_lock(row)
        content_quality_review = evaluate_content_quality_review(row)
        cover_media_quality_review = evaluate_cover_media_quality_review(row)

        warnings = _merge_warnings(
            showcase=showcase,
            bridge_blocking=bridge_rd.blocking_codes,
            bridge_missing=bridge_rd.missing_fields,
            catalog=catalog_preview,
            ai_fact_lock=ai_public_copy_review,
            content_quality=content_quality_review,
            cover_media_quality=cover_media_quality_review,
        )

        actions = _recommended_next_actions(
            offer=row,
            bridge_rd=bridge_rd,
            active_bridge=active_bridge_result,
            catalog=catalog_preview,
            has_active_execution_link=active_exec is not None,
            lifecycle_published=lifecycle_pub,
            ai_fact_lock=ai_public_copy_review,
            content_quality=content_quality_review,
        )

        active_link_read = (
            SupplierOfferExecutionLinkRead.model_validate(active_exec, from_attributes=True)
            if active_exec is not None
            else None
        )

        tour_row: Tour | None = None
        if active_bridge_result is not None:
            tour_row = session.get(Tour, active_bridge_result.tour_id)

        closure = _build_conversion_closure(
            offer=row,
            bridge_rd=bridge_rd,
            active_bridge=active_bridge_result,
            catalog=catalog_preview,
            active_exec=active_exec,
            lifecycle_pub=lifecycle_pub,
            can_create_exec=can_create,
            conv=conv,
            tour_row=tour_row,
            session=session,
        )

        bridge_readiness_read = AdminSupplierOfferBridgeReadinessRead(
            can_attempt_bridge=bridge_rd.can_attempt_bridge,
            missing_fields=bridge_rd.missing_fields,
            blocking_codes=bridge_rd.blocking_codes,
        )
        execution_links_read = AdminSupplierOfferExecutionLinksReviewRead(
            total_links_returned=len(all_links),
            active_link=active_link_read,
            can_create_execution_link=can_create,
            execution_link_precheck_note=exec_note,
        )
        operator_workflow = build_operator_workflow(
            tour_id=active_bridge_result.tour_id if active_bridge_result else None,
            packaging_status=offer_read.packaging_status,
            lifecycle_status=offer_read.lifecycle_status,
            closure=closure,
            bridge_readiness=bridge_readiness_read,
            linked_tour_catalog=linked_catalog,
            execution_links_review=execution_links_read,
            showcase_preview=showcase,
            ai_public_copy_review=ai_public_copy_review,
            content_quality_review=content_quality_review,
            cover_media_quality_review=cover_media_quality_review,
        )

        return AdminSupplierOfferReviewPackageRead(
            offer=offer_read,
            showcase_preview=showcase,
            bridge_readiness=bridge_readiness_read,
            active_tour_bridge=_bridge_result_to_read(active_bridge_result) if active_bridge_result else None,
            linked_tour_catalog=linked_catalog,
            execution_links_review=execution_links_read,
            mini_app_conversion_preview=mini_app,
            conversion_closure=closure,
            ai_public_copy_review=ai_public_copy_review,
            content_quality_review=content_quality_review,
            cover_media_quality_review=cover_media_quality_review,
            operator_workflow=operator_workflow,
            warnings=warnings,
            recommended_next_actions=actions,
        )


__all__ = ["SupplierOfferReviewPackageService", "SupplierOfferReviewPackageNotFoundError"]
