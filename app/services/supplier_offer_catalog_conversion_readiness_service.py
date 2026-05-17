"""A6A/A6B: build catalog/conversion readiness + guided actions from existing console reads only."""

from __future__ import annotations

from dataclasses import dataclass

from app.bot.constants import ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX
from app.schemas.admin_publishing_console import (
    AdminPublishingConsoleItemRead,
    AdminPublishingConsoleSupplierOfferDetailRead,
)
from app.schemas.supplier_offer_catalog_conversion_readiness import (
    CatalogConversionGuidedActionRead,
    CatalogConversionReadinessStatus,
    SupplierOfferCatalogConversionReadinessRead,
)


@dataclass(frozen=True)
class CatalogConversionReadinessContext:
    """Optional I/O-free hints from the cockpit assembler (e.g. Mini App base URL)."""

    mini_app_open_url: str | None = None


class SupplierOfferCatalogConversionReadinessService:
    """Side-effect free projection for supplier_offer_initial rows."""

    @staticmethod
    def _supplier_offer_id(item: AdminPublishingConsoleItemRead) -> int | None:
        if item.kind != "supplier_offer_initial":
            return None
        if item.offer_debug is not None:
            return int(item.offer_debug.supplier_offer_id)
        if item.source_kind == "supplier_offer" and item.source_id:
            return int(item.source_id)
        return None

    @classmethod
    def _guided_actions(
        cls,
        item: AdminPublishingConsoleItemRead,
        *,
        readiness_status: CatalogConversionReadinessStatus,
        context: CatalogConversionReadinessContext | None,
    ) -> list[CatalogConversionGuidedActionRead]:
        oid = cls._supplier_offer_id(item)
        if oid is None:
            return []
        ow_cb = f"{ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX}{oid}"
        actions: list[CatalogConversionGuidedActionRead] = []
        if readiness_status == "ready_for_review":
            actions.append(
                CatalogConversionGuidedActionRead(
                    label_message_key="admin_a6b_btn_verify_in_operator_workflow",
                    callback_data=ow_cb,
                )
            )
            url = (context.mini_app_open_url or "").strip() if context else ""
            if url:
                actions.append(
                    CatalogConversionGuidedActionRead(
                        label_message_key="admin_a6b_btn_open_mini_app",
                        url=url,
                    )
                )
        elif readiness_status in ("blocked", "needs_internal_preparation"):
            actions.append(
                CatalogConversionGuidedActionRead(
                    label_message_key="admin_a6b_btn_continue_in_operator_workflow",
                    callback_data=ow_cb,
                )
            )
        return actions

    @classmethod
    def build_from_console_item(
        cls,
        item: AdminPublishingConsoleItemRead,
        *,
        detail: AdminPublishingConsoleSupplierOfferDetailRead | None = None,
        context: CatalogConversionReadinessContext | None = None,
    ) -> SupplierOfferCatalogConversionReadinessRead | None:
        if item.kind != "supplier_offer_initial":
            return None

        cta = item.cta_safety_status
        mini_safe = cta == "exact_tour_ready"
        chain_st = item.prepare_conversion_chain_plan_status

        has_tour_link: bool | None
        has_exec: bool | None
        catalog_vis: bool | None
        if detail is not None:
            cs = detail.conversion_summary
            has_tour_link = cs.has_tour_bridge
            has_exec = cs.has_active_execution_link
            catalog_vis = cs.has_catalog_visible_tour
        else:
            has_tour_link, has_exec, catalog_vis = cls._infer_from_item_only(item)

        blocked = (
            item.console_status == "blocked"
            or cta == "media_blocked"
            or chain_st == "blocked"
        )

        warnings: list[str] = []
        if chain_st == "partial":
            warnings.append("admin_a6a_warn_prepare_partial")

        main_blocker: str | None = None
        next_step: str
        readiness: CatalogConversionReadinessStatus

        if blocked:
            readiness = "blocked"
            status_key = "admin_a6a_status_blocked"
            if cta == "media_blocked":
                main_blocker = "admin_a6a_blocker_media_gate"
                next_step = "admin_a6a_next_fix_media"
            elif chain_st == "blocked":
                main_blocker = "admin_a6a_blocker_prepare_chain"
                next_step = "admin_a6a_next_review_prepare_chain"
            elif cta == "missing_execution_link":
                main_blocker = "admin_a6a_blocker_offer_tour_link"
                next_step = "admin_a6a_next_prepare_offer_tour_link"
            elif cta == "tour_not_listed":
                main_blocker = "admin_a6a_blocker_catalog_route"
                next_step = "admin_a6a_next_check_catalog"
            elif item.console_status == "blocked":
                main_blocker = "admin_a6a_blocker_console"
                next_step = "admin_a6a_next_resolve_console"
            else:
                main_blocker = "admin_a6a_blocker_generic"
                next_step = "admin_a6a_next_internal_review"
        elif mini_safe and (catalog_vis is not False):
            readiness = "ready_for_review"
            status_key = "admin_a6a_status_ready_for_review"
            main_blocker = None
            next_step = "admin_a6a_next_verify_mini_app"
        else:
            readiness = "needs_internal_preparation"
            status_key = "admin_a6a_status_needs_preparation"
            if cta == "missing_execution_link":
                main_blocker = "admin_a6a_blocker_offer_tour_link"
                next_step = "admin_a6a_next_prepare_offer_tour_link"
            elif cta == "tour_not_listed":
                main_blocker = "admin_a6a_blocker_catalog_route"
                next_step = "admin_a6a_next_check_catalog"
            elif item.conversion_target_kind == "none":
                main_blocker = "admin_a6a_blocker_no_conversion_target"
                next_step = "admin_a6a_next_prepare_offer_tour_link"
            else:
                main_blocker = "admin_a6a_blocker_needs_setup"
                next_step = "admin_a6a_next_complete_in_admin"

        guided = cls._guided_actions(item, readiness_status=readiness, context=context)

        return SupplierOfferCatalogConversionReadinessRead(
            readiness_status=readiness,
            status_label_message_key=status_key,
            main_blocker_message_key=main_blocker,
            warnings_message_keys=warnings[:2],
            next_step_message_key=next_step,
            has_tour_link=has_tour_link,
            has_execution_link=has_exec,
            mini_app_cta_safe=mini_safe,
            catalog_visible=catalog_vis,
            guided_actions=guided,
        )

    @staticmethod
    def _infer_from_item_only(
        item: AdminPublishingConsoleItemRead,
    ) -> tuple[bool | None, bool | None, bool | None]:
        """Best-effort booleans when supplier-offer detail was not loaded."""
        cta = item.cta_safety_status
        if cta == "exact_tour_ready":
            return True, True, None
        if cta == "missing_execution_link":
            return False, False, None
        if cta == "tour_not_listed":
            return True, None, False
        if item.conversion_target_kind == "exact_tour":
            return None, None, None
        if item.conversion_target_kind == "none":
            return False, False, None
        return None, None, None


__all__ = [
    "CatalogConversionReadinessContext",
    "SupplierOfferCatalogConversionReadinessService",
]
