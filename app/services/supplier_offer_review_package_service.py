"""Read-only admin aggregation for supplier offer review before bridge/catalog/showcase steps."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository
from app.schemas.supplier_admin import (
    AdminSupplierOfferBridgeReadinessRead,
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
from app.services.mini_app_supplier_offer_landing import MiniAppSupplierOfferLandingService
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
    return out


def _recommended_next_actions(
    *,
    offer: SupplierOffer,
    bridge_rd: SupplierOfferBridgeMaterializationReadiness,
    active_bridge: SupplierOfferTourBridgeResult | None,
    catalog: TourCatalogActivationPreview | None,
    has_active_execution_link: bool,
    lifecycle_published: bool,
) -> list[str]:
    actions: list[str] = []
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

        warnings = _merge_warnings(
            showcase=showcase,
            bridge_blocking=bridge_rd.blocking_codes,
            bridge_missing=bridge_rd.missing_fields,
            catalog=catalog_preview,
        )

        actions = _recommended_next_actions(
            offer=row,
            bridge_rd=bridge_rd,
            active_bridge=active_bridge_result,
            catalog=catalog_preview,
            has_active_execution_link=active_exec is not None,
            lifecycle_published=lifecycle_pub,
        )

        active_link_read = (
            SupplierOfferExecutionLinkRead.model_validate(active_exec, from_attributes=True)
            if active_exec is not None
            else None
        )

        return AdminSupplierOfferReviewPackageRead(
            offer=offer_read,
            showcase_preview=showcase,
            bridge_readiness=AdminSupplierOfferBridgeReadinessRead(
                can_attempt_bridge=bridge_rd.can_attempt_bridge,
                missing_fields=bridge_rd.missing_fields,
                blocking_codes=bridge_rd.blocking_codes,
            ),
            active_tour_bridge=_bridge_result_to_read(active_bridge_result) if active_bridge_result else None,
            linked_tour_catalog=linked_catalog,
            execution_links_review=AdminSupplierOfferExecutionLinksReviewRead(
                total_links_returned=len(all_links),
                active_link=active_link_read,
                can_create_execution_link=can_create,
                execution_link_precheck_note=exec_note,
            ),
            mini_app_conversion_preview=mini_app,
            warnings=warnings,
            recommended_next_actions=actions,
        )


__all__ = ["SupplierOfferReviewPackageService", "SupplierOfferReviewPackageNotFoundError"]
