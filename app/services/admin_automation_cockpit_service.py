"""A1-Block 1: read-only Admin Automation Cockpit assembly (publishing-console projection only; no I/O)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle
from app.schemas.admin_automation_cockpit import (
    AdminAutomationCockpitCardRead,
    AdminAutomationCockpitCardSafetyFlagsRead,
    AdminAutomationCockpitQueryRead,
    AdminAutomationCockpitQueueRead,
    AdminAutomationCockpitRead,
    AdminAutomationCockpitSafetySummaryRead,
    AdminAutomationCockpitSummaryRead,
    AutomationCockpitQueueCode,
    AutomationCockpitQueueTone,
    CockpitNextBestActionKind,
)
from app.schemas.admin_publishing_console import AdminPublishingConsoleItemRead, PublishingConsoleUiPrimaryActionKind
from app.services.admin_publishing_console_service import AdminPublishingConsoleService

_CARD_SAFETY = AdminAutomationCockpitCardSafetyFlagsRead()


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


def _classify_queue(item: AdminPublishingConsoleItemRead) -> AutomationCockpitQueueCode:
    """Conservative single-queue assignment; prefers existing publishing-console signals."""
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


def _cockpit_next_action(
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
        oid = item.offer_debug.supplier_offer_id if item.offer_debug else item.source_id
        if oid:
            paths["publishing_console_detail_path"] = f"/admin/publishing-console/supplier-offers/{oid}"
            paths["publishing_console_editor_path"] = f"/admin/publishing-console/supplier-offers/{oid}/editor"
    if item.admin_tour_path:
        paths["admin_tour_path"] = item.admin_tour_path
    if item.admin_action_path:
        paths["admin_action_path"] = item.admin_action_path
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


def _build_card(item: AdminPublishingConsoleItemRead, queue: AutomationCockpitQueueCode) -> AdminAutomationCockpitCardRead:
    ncode, nlabel, nkind, nenabled = _cockpit_next_action(item)
    if nkind not in ("safe_read", "future_disabled"):
        nkind = "future_disabled"
        nenabled = False
    if nkind == "future_disabled":
        nenabled = False

    st = item.source_kind
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
        source_type=st,
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
}


class AdminAutomationCockpitService:
    """Assembles the cockpit strictly from ``AdminPublishingConsoleService.read_console`` (read-only)."""

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

        by_queue: dict[AutomationCockpitQueueCode, list[AdminPublishingConsoleItemRead]] = {
            "supplier_intake": [],
            "missing_info": [],
            "offer_readiness": [],
            "risk_conflict": [],
        }
        for it in items:
            q = _classify_queue(it)
            by_queue[q].append(it)

        def sort_key(i: AdminPublishingConsoleItemRead) -> tuple[int, str]:
            return (_priority(i.console_status), i.candidate_key)

        queues_out: list[AdminAutomationCockpitQueueRead] = []

        future_disabled_cards = 0
        for qcode in ("supplier_intake", "missing_info", "offer_readiness", "risk_conflict"):
            label, desc, tone = _QUEUE_COPY[qcode]
            bucket = by_queue[qcode]
            bucket_sorted = sorted(bucket, key=sort_key)
            cards: list[AdminAutomationCockpitCardRead] = []
            if include_queues is None or qcode in include_queues:
                for it in bucket_sorted[:per_q]:
                    c = _build_card(it, qcode)
                    cards.append(c)
                    if c.next_best_action_kind == "future_disabled":
                        future_disabled_cards += 1

            qs: AutomationCockpitQueueRead = AdminAutomationCockpitQueueRead(
                queue_code=qcode,
                queue_label=label,
                queue_status="active" if bucket_sorted else "idle",
                queue_tone=tone,
                total_count=len(bucket_sorted),
                cards=cards,
                description=desc,
                next_refresh_hint="Re-fetch publishing-console snapshot; counts follow console fetch limits.",
            )
            queues_out.append(qs)

        total = len(items)
        qc = {k: len(by_queue[k]) for k in by_queue}
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
                "A1-Block 1 cockpit GET: read-only snapshot from publishing console; "
                "no Telegram I/O, publish, scheduler jobs, supplier sends, QR, Layer A, or B11 changes."
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
                "Queue assignments derive from existing publishing-console rows "
                f"(read_console limit={fetch_limit}); totals exclude offers/tours beyond that snapshot."
            ),
            query=qmeta,
        )