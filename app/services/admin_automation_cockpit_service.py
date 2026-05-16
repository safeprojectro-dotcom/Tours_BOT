"""A1-Block 1/2: read-only Admin Automation Cockpit assembly (publishing-console + optional detail reads; no I/O)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle
from app.schemas.admin_automation_cockpit import (
    AdminAutomationCockpitCardRead,
    AdminAutomationCockpitCardSafetyFlagsRead,
    AdminAutomationCockpitCommercialContextRead,
    AdminAutomationCockpitQueryRead,
    AdminAutomationCockpitQueueRead,
    AdminAutomationCockpitRead,
    AdminAutomationCockpitSafetySummaryRead,
    AdminAutomationCockpitSummaryRead,
    AutomationCockpitQueueCode,
    AutomationCockpitQueueTone,
    COCKPIT_FACT_LOCK_NOTE,
    CockpitNextBestActionKind,
)
from app.schemas.admin_publishing_console import (
    AdminPublishingConsoleItemRead,
    AdminPublishingConsoleSupplierOfferDetailRead,
    PublishingConsoleUiPrimaryActionKind,
)
from app.services.admin_publishing_console_service import AdminPublishingConsoleService

_CARD_SAFETY = AdminAutomationCockpitCardSafetyFlagsRead()

OPERATIONAL_QUEUES: tuple[AutomationCockpitQueueCode, ...] = (
    "supplier_intake",
    "missing_info",
    "offer_readiness",
    "risk_conflict",
)
COMMERCIAL_QUEUES: tuple[AutomationCockpitQueueCode, ...] = (
    "marketing_review",
    "publishing_queue",
    "catalog_conversion",
)
ALL_QUEUE_ORDER: tuple[AutomationCockpitQueueCode, ...] = OPERATIONAL_QUEUES + COMMERCIAL_QUEUES

CommercialLane = Literal["marketing_review", "publishing_queue", "catalog_conversion"]


def _supplier_offer_id(item: AdminPublishingConsoleItemRead) -> int | None:
    if item.kind != "supplier_offer_initial":
        return None
    if item.offer_debug is None:
        return item.source_id or None
    return item.offer_debug.supplier_offer_id


def _detail_for_offer(
    console: AdminPublishingConsoleService,
    session: Session,
    cache: dict[int, AdminPublishingConsoleSupplierOfferDetailRead | None],
    offer_id: int,
) -> AdminPublishingConsoleSupplierOfferDetailRead | None:
    if offer_id not in cache:
        cache[offer_id] = console.read_supplier_offer_detail(session, offer_id=offer_id)
    return cache[offer_id]


def _lifecycle_value(item: AdminPublishingConsoleItemRead) -> str:
    od = item.offer_debug
    if od is None:
        return ""
    ls = od.lifecycle_status
    return ls.value if hasattr(ls, "value") else str(ls)


def _packaging_value(item: AdminPublishingConsoleItemRead) -> str:
    od = item.offer_debug
    if od is None:
        return ""
    ps = od.packaging_status
    return ps.value if hasattr(ps, "value") else str(ps)


def _has_blockers(item: AdminPublishingConsoleItemRead) -> bool:
    pr = item.publish_readiness
    if (pr.primary_blocker or "").strip():
        return True
    if item.preview_payload.blockers:
        return True
    if item.blocked_reasons:
        return True
    if item.ui_card.blocker_line and str(item.ui_card.blocker_line).strip():
        return True
    return False


def _has_meaningful_warnings(item: AdminPublishingConsoleItemRead) -> bool:
    pr = item.publish_readiness
    if (pr.warning_summary or "").strip():
        return True
    if item.preview_payload.warnings:
        return True
    if item.ui_card.warning_line and str(item.ui_card.warning_line).strip():
        return True
    return False


def _cta_problematic(item: AdminPublishingConsoleItemRead) -> bool:
    return item.cta_safety_status in (
        "missing_execution_link",
        "tour_not_listed",
        "media_blocked",
    )


def _classify_operational_queue(item: AdminPublishingConsoleItemRead) -> AutomationCockpitQueueCode:
    """Block 1 operational lanes only."""
    if item.kind == "tour_promotion":
        if item.console_status == "blocked":
            return "missing_info"
        if item.console_status == "needs_attention":
            return "risk_conflict"
        if item.console_status == "ready":
            return "offer_readiness"
        return "risk_conflict"

    life = _lifecycle_value(item)
    pack = _packaging_value(item)
    pr = item.publish_readiness
    blockers = _has_blockers(item)

    if pr.status == "needs_review":
        return "risk_conflict"

    if pr.status == "already_published":
        if blockers or _cta_problematic(item) or _has_meaningful_warnings(item):
            return "risk_conflict"
        return "offer_readiness"

    if item.console_status == "ready" and blockers and pr.status == "ready_to_suggest":
        return "risk_conflict"

    if pack in ("clarification_requested", "packaging_rejected"):
        return "missing_info"

    if life == SupplierOfferLifecycle.REJECTED.value:
        return "missing_info"

    if item.console_status == "blocked" or pr.status == "blocked" or blockers:
        return "missing_info"

    if life == SupplierOfferLifecycle.DRAFT.value:
        return "supplier_intake"

    if pack in (
        "none",
        "packaging_pending",
        "packaging_generated",
        "needs_admin_review",
        "",
    ):
        return "supplier_intake"

    if item.console_status == "ready" and pr.status == "ready_to_suggest":
        return "offer_readiness"

    if item.console_status == "ready":
        return "offer_readiness"

    if item.console_status == "needs_attention":
        return "risk_conflict"

    return "risk_conflict"


def _priority(console_status: str) -> int:
    if console_status == "blocked":
        return 1
    if console_status == "needs_attention":
        return 2
    if console_status == "ready":
        return 3
    return 5


def _cockpit_next_action_operational(
    item: AdminPublishingConsoleItemRead,
) -> tuple[str, str, CockpitNextBestActionKind, bool]:
    ui = item.ui_card
    pk: PublishingConsoleUiPrimaryActionKind = ui.primary_action_kind
    if pk == "guarded_post":
        return (
            ui.primary_action_code or "guarded_internal_action",
            ui.primary_action_label or "Guarded internal action",
            "future_disabled",
            False,
        )
    if pk == "future":
        return (
            ui.primary_action_code or "future_capability",
            ui.primary_action_label or "Future capability",
            "future_disabled",
            False,
        )
    if pk == "safe_read":
        code = ui.primary_action_code or "safe_read"
        label = ui.primary_action_label or "Open"
        return (code, label, "safe_read", bool(ui.primary_action_enabled))

    code = item.publish_readiness.next_action_code or "review_publishing_context"
    label = item.publish_readiness.next_action_label or "Review publishing context"
    path_ok = bool(item.review_package_path or item.admin_tour_path or item.admin_action_path)
    return (code, label, "safe_read", path_ok)


def _normalize_action(
    code: str,
    label: str,
    kind: CockpitNextBestActionKind,
    enabled: bool,
) -> tuple[str, str, CockpitNextBestActionKind, bool]:
    if kind not in ("safe_read", "future_disabled"):
        return code, label, "future_disabled", False
    if kind == "future_disabled":
        return code, label, "future_disabled", False
    return code, label, kind, enabled


def _risk_summary(item: AdminPublishingConsoleItemRead, queue: AutomationCockpitQueueCode) -> str | None:
    if queue != "risk_conflict":
        return None
    parts: list[str] = []
    if item.publish_readiness.status == "needs_review":
        parts.append("Publish readiness flagged for manual review.")
    if item.cta_safety_status not in ("exact_tour_ready", "already_published", "not_applicable"):
        parts.append(f"CTA safety: {item.cta_safety_status}.")
    if not parts:
        parts.append("Ambiguous or non-standard publishing-console posture; verify in review-package context.")
    return " ".join(parts)[:500]


def _source_paths(item: AdminPublishingConsoleItemRead) -> dict[str, str]:
    paths: dict[str, str] = {}
    if item.review_package_path:
        paths["review_package_path"] = item.review_package_path
    if item.prepare_conversion_chain_plan_path:
        paths["prepare_conversion_chain_plan_path"] = item.prepare_conversion_chain_plan_path
    if item.kind == "supplier_offer_initial":
        oid = _supplier_offer_id(item)
        if oid:
            paths["publishing_console_detail_path"] = f"/admin/publishing-console/supplier-offers/{oid}"
            paths["publishing_console_editor_path"] = f"/admin/publishing-console/supplier-offers/{oid}/editor"
    if item.admin_tour_path:
        paths["admin_tour_path"] = item.admin_tour_path
    if item.admin_action_path:
        paths["admin_action_path"] = item.admin_action_path
    if item.preview_path:
        paths["preview_path"] = item.preview_path
    return paths


def _blocker_line(item: AdminPublishingConsoleItemRead) -> str | None:
    pr = item.publish_readiness
    line = (item.ui_card.blocker_line or "").strip() or (pr.primary_blocker or "").strip()
    if line:
        return line[:500]
    if item.preview_payload.blockers:
        return str(item.preview_payload.blockers[0])[:500]
    if item.blocked_reasons:
        return str(item.blocked_reasons[0])[:500]
    return None


def _warning_line(item: AdminPublishingConsoleItemRead) -> str | None:
    pr = item.publish_readiness
    line = (item.ui_card.warning_line or "").strip() or (pr.warning_summary or "").strip()
    if line:
        return line[:500]
    if item.preview_payload.warnings:
        return str(item.preview_payload.warnings[0])[:500]
    return None


def _operational_commercial_stub(item: AdminPublishingConsoleItemRead) -> AdminAutomationCockpitCommercialContextRead | None:
    oid = _supplier_offer_id(item)
    if oid is None:
        return None
    return AdminAutomationCockpitCommercialContextRead(
        supplier_offer_id=oid,
        fact_lock_note=COCKPIT_FACT_LOCK_NOTE,
    )


def _commercial_context(
    item: AdminPublishingConsoleItemRead,
    detail: AdminPublishingConsoleSupplierOfferDetailRead | None,
) -> AdminAutomationCockpitCommercialContextRead:
    ctx = AdminAutomationCockpitCommercialContextRead(fact_lock_note=COCKPIT_FACT_LOCK_NOTE)
    oid = _supplier_offer_id(item)
    if oid is not None:
        ctx.supplier_offer_id = oid
    if item.tour_debug is not None:
        ctx.tour_id = item.tour_debug.tour_id
        ctx.tour_code = item.tour_debug.tour_code
    ctx.preview_status = str(item.console_preview.preview_status)
    ctx.payload_status = str(item.preview_payload.payload_status)
    ctx.template_family = str(item.console_preview.template_family)
    ctx.selected_template_id = item.template_library.selected_template_id or item.template_library.recommended_template_id
    ctx.publish_status = str(item.publish_readiness.status)
    ctx.prepare_chain_status = item.prepare_conversion_chain_plan_status
    if detail is not None:
        ctx.already_published = detail.publication_summary.already_published
        ctx.has_tour_bridge = detail.conversion_summary.has_tour_bridge
        ctx.has_catalog_visible_tour = detail.conversion_summary.has_catalog_visible_tour
        ctx.has_active_execution_link = detail.conversion_summary.has_active_execution_link
    return ctx


def _template_lane_blocked(item: AdminPublishingConsoleItemRead) -> bool:
    return any(getattr(e, "status", "") == "blocked" for e in item.template_library.available_templates)


def _marketing_review_action(
    item: AdminPublishingConsoleItemRead,
) -> tuple[str, str, CockpitNextBestActionKind, bool]:
    tpl = item.template_library
    pay = item.preview_payload
    cp = item.console_preview

    paths = bool(item.review_package_path or item.preview_path)
    editor_ok = bool(_supplier_offer_id(item))

    if pay.payload_status in ("blocked", "not_applicable"):
        return ("review_missing_marketing_data", "Review missing marketing data", "safe_read", paths)
    if item.kind == "supplier_offer_initial" and pay.payload_status in ("placeholder",) and not pay.body_text:
        return ("review_missing_marketing_data", "Review missing marketing data", "safe_read", paths)

    if _template_lane_blocked(item):
        return ("review_template", "Review template variants", "safe_read", paths)

    if tpl.available_templates and not (tpl.selected_template_id or tpl.recommended_template_id):
        if any(getattr(e, "status", "") == "future" for e in tpl.available_templates):
            return ("review_template", "Review template selection", "safe_read", paths)

    payload_ok = pay.payload_status == "available"
    template_sel = bool(tpl.selected_template_id or tpl.recommended_template_id)
    if payload_ok and template_sel:
        if item.kind == "supplier_offer_initial":
            return ("open_marketing_review", "Open marketing review", "safe_read", editor_ok)
        return ("open_marketing_review", "Open promotion context", "safe_read", bool(item.admin_tour_path))

    if cp.preview_status == "available" and (cp.preview_path or item.preview_path):
        return ("open_preview", "Open preview", "safe_read", bool(cp.preview_path or item.preview_path))

    return ("future_edit_marketing_copy", "Edit marketing copy (future)", "future_disabled", False)


def _publishing_queue_action(
    item: AdminPublishingConsoleItemRead,
    detail: AdminPublishingConsoleSupplierOfferDetailRead | None,
) -> tuple[str, str, CockpitNextBestActionKind, bool]:
    pr = item.publish_readiness
    already = bool(detail.publication_summary.already_published) if detail is not None else pr.status == "already_published"

    if already:
        if detail is not None and (detail.conversion_summary.has_active_execution_link is False):
            return ("review_conversion_health", "Review conversion after publish", "safe_read", True)
        return ("review_already_published", "Review published showcase state", "safe_read", True)
    if pr.can_suggest_manual_publish and pr.status == "ready_to_suggest":
        return ("review_publish_readiness", "Review publish readiness", "safe_read", True)
    if pr.status == "blocked" or item.console_status == "blocked":
        return ("resolve_publish_blocker", "Resolve publish blocker", "safe_read", True)
    if pr.status == "needs_review":
        return ("await_publish_go_no_go", "Await publish go/no-go", "future_disabled", False)
    if pr.status == "not_applicable" and item.kind == "tour_promotion":
        return ("review_publish_readiness", "Review tour promotion readiness", "safe_read", bool(item.admin_tour_path))
    return ("future_confirm_publish", "Confirm channel publish (future)", "future_disabled", False)


def _catalog_conversion_action(
    item: AdminPublishingConsoleItemRead,
    detail: AdminPublishingConsoleSupplierOfferDetailRead | None,
) -> tuple[str, str, CockpitNextBestActionKind, bool]:
    if item.kind == "tour_promotion":
        td = item.tour_debug
        if td is not None and td.catalog_customer_visible:
            return ("review_conversion_health", "Review catalog promotion health", "safe_read", bool(item.admin_tour_path))
        return ("review_catalog_visibility", "Review catalog visibility", "safe_read", bool(item.admin_tour_path))

    cc = detail.conversion_summary if detail is not None else None
    plan_path = bool(item.prepare_conversion_chain_plan_path)

    if cc is None:
        return ("open_prepare_chain_plan", "Open prepare conversion plan", "safe_read", plan_path)

    bridge = bool(cc.has_tour_bridge)
    cat = bool(cc.has_catalog_visible_tour)
    exe = bool(cc.has_active_execution_link)

    if bridge and cat and exe:
        return ("review_conversion_health", "Review conversion chain health", "safe_read", True)

    if item.prepare_conversion_chain_action is not None and item.prepare_conversion_chain_action.enabled:
        return ("run_conversion_dry_run_future", "Prepare conversion dry-run (future)", "future_disabled", False)

    if not bridge or not cat or not exe:
        step = (cc.next_missing_step or "").strip()
        if step:
            return (
                "resolve_conversion_blocker",
                f"Resolve conversion: {step[:120]}",
                "safe_read",
                plan_path or bool(item.review_package_path),
            )
        return ("open_prepare_chain_plan", "Open prepare conversion plan", "safe_read", plan_path)

    return ("review_conversion_health", "Review conversion context", "safe_read", True)


def _marketing_sort_key(item: AdminPublishingConsoleItemRead) -> tuple[int, int, str]:
    pay = item.preview_payload.payload_status
    if pay in ("blocked", "not_applicable"):
        tier = 0
    elif pay == "placeholder":
        tier = 1
    else:
        tier = 2
    if _template_lane_blocked(item):
        tier = min(tier, 1)
    return (tier, _priority(item.console_status), item.candidate_key)


def _publishing_sort_key(item: AdminPublishingConsoleItemRead) -> tuple[int, int, str]:
    pr = item.publish_readiness
    if pr.status == "blocked" or item.console_status == "blocked":
        tier = 0
    elif pr.status == "ready_to_suggest":
        tier = 2
    elif pr.status == "already_published":
        tier = 3
    else:
        tier = 1
    return (tier, _priority(item.console_status), item.candidate_key)


def _catalog_sort_key_item_only(item: AdminPublishingConsoleItemRead) -> tuple[int, int, str]:
    if item.kind == "tour_promotion":
        td = item.tour_debug
        tier = 2 if td is not None and td.catalog_customer_visible else 0
        return (tier, _priority(item.console_status), item.candidate_key)
    st = item.prepare_conversion_chain_plan_status
    if st == "already_prepared":
        tier = 2
    elif st in ("blocked", "ineligible"):
        tier = 0
    elif st == "partial":
        tier = 1
    else:
        tier = 1
    if item.cta_safety_status == "exact_tour_ready":
        tier = max(tier, 2)
    return (tier, _priority(item.console_status), item.candidate_key)


def _build_operational_card(
    item: AdminPublishingConsoleItemRead,
    queue: AutomationCockpitQueueCode,
) -> AdminAutomationCockpitCardRead:
    ncode, nlabel, nkind, nenabled = _cockpit_next_action_operational(item)
    ncode, nlabel, nkind, nenabled = _normalize_action(ncode, nlabel, nkind, nenabled)

    sid = item.source_id
    if item.kind == "tour_promotion" and item.tour_debug is not None:
        sid = item.tour_debug.tour_id

    meta: dict[str, Any] = {
        "candidate_key": item.candidate_key,
        "kind": item.kind,
        "console_status": item.console_status,
        "publish_readiness_status": item.publish_readiness.status,
        "cockpit_queue": queue,
    }

    return AdminAutomationCockpitCardRead(
        card_id=f"{queue}:{item.candidate_key}",
        source_type=item.source_kind,
        source_id=int(sid),
        title=item.title,
        subtitle=item.subtitle,
        status=item.console_status,
        status_label=item.ui_card.status_label,
        status_tone=item.ui_card.status_tone,
        priority=_priority(item.console_status),
        next_best_action_code=ncode,
        next_best_action_label=nlabel,
        next_best_action_kind=nkind,
        next_best_action_enabled=nenabled,
        blocker_summary=_blocker_line(item),
        warning_summary=_warning_line(item),
        risk_summary=_risk_summary(item, queue),
        owner_role="admin_operator",
        last_updated_at=item.publish_readiness.generated_at,
        due_at=None,
        departure_at=None,
        safety_flags=_CARD_SAFETY,
        source_paths=_source_paths(item),
        commercial_context=_operational_commercial_stub(item),
        metadata=meta,
    )


def _build_commercial_card(
    item: AdminPublishingConsoleItemRead,
    lane: CommercialLane,
    *,
    console: AdminPublishingConsoleService,
    session: Session,
    detail_cache: dict[int, AdminPublishingConsoleSupplierOfferDetailRead | None],
) -> AdminAutomationCockpitCardRead:
    detail: AdminPublishingConsoleSupplierOfferDetailRead | None = None
    oid = _supplier_offer_id(item)
    if oid is not None:
        detail = _detail_for_offer(console, session, detail_cache, oid)

    if lane == "marketing_review":
        ncode, nlabel, nkind, nenabled = _marketing_review_action(item)
    elif lane == "publishing_queue":
        ncode, nlabel, nkind, nenabled = _publishing_queue_action(item, detail)
    else:
        ncode, nlabel, nkind, nenabled = _catalog_conversion_action(item, detail)
    ncode, nlabel, nkind, nenabled = _normalize_action(ncode, nlabel, nkind, nenabled)

    sid = item.source_id
    if item.kind == "tour_promotion" and item.tour_debug is not None:
        sid = item.tour_debug.tour_id

    meta: dict[str, Any] = {
        "candidate_key": item.candidate_key,
        "kind": item.kind,
        "console_status": item.console_status,
        "commercial_lane": lane,
        "publish_readiness_status": item.publish_readiness.status,
    }

    return AdminAutomationCockpitCardRead(
        card_id=f"{lane}:{item.candidate_key}",
        source_type=item.source_kind,
        source_id=int(sid),
        title=item.title,
        subtitle=item.subtitle,
        status=item.console_status,
        status_label=item.ui_card.status_label,
        status_tone=item.ui_card.status_tone,
        priority=_priority(item.console_status),
        next_best_action_code=ncode,
        next_best_action_label=nlabel,
        next_best_action_kind=nkind,
        next_best_action_enabled=nenabled,
        blocker_summary=_blocker_line(item),
        warning_summary=_warning_line(item),
        risk_summary=None,
        owner_role="admin_operator",
        last_updated_at=item.publish_readiness.generated_at,
        due_at=None,
        departure_at=None,
        safety_flags=_CARD_SAFETY,
        source_paths=_source_paths(item),
        commercial_context=_commercial_context(item, detail),
        metadata=meta,
    )


_QUEUE_COPY: dict[AutomationCockpitQueueCode, tuple[str, str, AutomationCockpitQueueTone]] = {
    "supplier_intake": (
        "Supplier intake",
        "Supplier offers still in early lifecycle / packaging before steady operational processing.",
        "warning",
    ),
    "missing_info": (
        "Missing info / clarification",
        "Rows with blockers, rejected/clarification packaging, or failed readiness gates.",
        "danger",
    ),
    "offer_readiness": (
        "Offer readiness",
        "Rows that look ready for the next internal publishing / conversion step (read-only hints).",
        "success",
    ),
    "risk_conflict": (
        "Risk / conflict",
        "Ambiguous posture, needs_review readiness, attention state, or follow-ups after publish.",
        "warning",
    ),
    "marketing_review": (
        "Marketing review",
        "Packaging, template, and preview payload posture for admin marketing review (read-only).",
        "info",
    ),
    "publishing_queue": (
        "Publishing queue",
        "Channel publish readiness and publication state (read-only; no send from this GET).",
        "warning",
    ),
    "catalog_conversion": (
        "Catalog / conversion",
        "Tour bridge, catalog listing, execution link, and prepare-chain hints (read-only).",
        "info",
    ),
}


class AdminAutomationCockpitService:
    """Assembles the cockpit from publishing console list rows + selective supplier-offer detail reads."""

    def __init__(self, *, publishing_console: AdminPublishingConsoleService | None = None) -> None:
        self._console = publishing_console or AdminPublishingConsoleService()

    def read_cockpit(
        self,
        session: Session,
        *,
        limit_per_queue: int = 20,
        include_queues: frozenset[str] | None = None,
    ) -> AdminAutomationCockpitRead:
        per_q = max(1, min(limit_per_queue, 100))
        fetch_limit = min(500, max(120, per_q * 12))
        snap = self._console.read_console(session, limit=fetch_limit, kind=None)
        items = snap.items

        by_operational: dict[AutomationCockpitQueueCode, list[AdminPublishingConsoleItemRead]] = {
            "supplier_intake": [],
            "missing_info": [],
            "offer_readiness": [],
            "risk_conflict": [],
        }
        for it in items:
            q = _classify_operational_queue(it)
            by_operational[q].append(it)

        commercial_buckets: dict[CommercialLane, list[AdminPublishingConsoleItemRead]] = {
            "marketing_review": list(items),
            "publishing_queue": list(items),
            "catalog_conversion": list(items),
        }

        def op_sort_key(i: AdminPublishingConsoleItemRead) -> tuple[int, str]:
            return (_priority(i.console_status), i.candidate_key)

        detail_cache: dict[int, AdminPublishingConsoleSupplierOfferDetailRead | None] = {}

        queues_out: list[AdminAutomationCockpitQueueRead] = []
        future_disabled_cards = 0

        for qcode in ALL_QUEUE_ORDER:
            label, desc, tone = _QUEUE_COPY[qcode]
            bucket_sorted: list[AdminPublishingConsoleItemRead]
            if qcode in OPERATIONAL_QUEUES:
                bucket_sorted = sorted(by_operational[qcode], key=op_sort_key)
            elif qcode == "marketing_review":
                bucket_sorted = sorted(commercial_buckets["marketing_review"], key=_marketing_sort_key)
            elif qcode == "publishing_queue":
                bucket_sorted = sorted(commercial_buckets["publishing_queue"], key=_publishing_sort_key)
            else:
                bucket_sorted = sorted(
                    commercial_buckets["catalog_conversion"],
                    key=_catalog_sort_key_item_only,
                )

            cards: list[AdminAutomationCockpitCardRead] = []
            if include_queues is None or qcode in include_queues:
                for it in bucket_sorted[:per_q]:
                    if qcode in OPERATIONAL_QUEUES:
                        c = _build_operational_card(it, qcode)
                    elif qcode == "marketing_review":
                        c = _build_commercial_card(
                            it,
                            "marketing_review",
                            console=self._console,
                            session=session,
                            detail_cache=detail_cache,
                        )
                    elif qcode == "publishing_queue":
                        c = _build_commercial_card(
                            it,
                            "publishing_queue",
                            console=self._console,
                            session=session,
                            detail_cache=detail_cache,
                        )
                    else:
                        c = _build_commercial_card(
                            it,
                            "catalog_conversion",
                            console=self._console,
                            session=session,
                            detail_cache=detail_cache,
                        )
                    cards.append(c)
                    if c.next_best_action_kind == "future_disabled":
                        future_disabled_cards += 1

            qs = AdminAutomationCockpitQueueRead(
                queue_code=qcode,
                queue_label=label,
                queue_status="active" if bucket_sorted else "idle",
                queue_tone=tone,
                total_count=len(bucket_sorted),
                cards=cards,
                description=desc,
                next_refresh_hint="Re-fetch publishing-console snapshot; commercial lanes may load per-offer detail reads.",
            )
            queues_out.append(qs)

        total = len(items)
        qc: dict[str, int] = {k: len(by_operational[k]) for k in OPERATIONAL_QUEUES}
        qc["marketing_review"] = len(commercial_buckets["marketing_review"])
        qc["publishing_queue"] = len(commercial_buckets["publishing_queue"])
        qc["catalog_conversion"] = len(commercial_buckets["catalog_conversion"])

        blocked_n = sum(1 for i in items if i.console_status == "blocked")
        needs_n = sum(1 for i in items if i.console_status == "needs_attention")
        ready_n = sum(1 for i in items if i.console_status == "ready")
        urgent_n = sum(1 for i in items if i.console_status in ("blocked", "needs_attention"))

        summary = AdminAutomationCockpitSummaryRead(
            total_cards=total,
            queue_counts=qc,
            urgent_count=urgent_n,
            needs_attention_count=needs_n,
            ready_count=ready_n,
            blocked_count=blocked_n,
            future_disabled_count=future_disabled_cards,
        )

        safety = AdminAutomationCockpitSafetySummaryRead(
            note=(
                "A1-Block 1/2 cockpit GET: read-only snapshot; commercial lanes add in-process supplier-offer detail "
                "reads only. No Telegram I/O, publish, scheduler jobs, supplier sends, QR, Layer A, B11, AI tools, "
                "or external calls."
            ),
        )

        qmeta = AdminAutomationCockpitQueryRead(
            limit_per_queue=per_q,
            include_queues=sorted(include_queues) if include_queues is not None else None,
            publishing_console_limit=fetch_limit,
            publishing_console_kind=None,
        )

        return AdminAutomationCockpitRead(
            generated_at=datetime.now(UTC),
            summary=summary,
            queues=queues_out,
            safety_summary=safety,
            source_note=(
                "Operational queues classify each publishing-console row once. "
                "Commercial lanes (marketing / publishing / catalog) may list the same row for flow context. "
                "Supplier-offer detail is loaded for commercial cards and catalog ordering (bounded by per-queue card limits). "
                f"Publishing console snapshot limit={fetch_limit}."
            ),
            query=qmeta,
        )
