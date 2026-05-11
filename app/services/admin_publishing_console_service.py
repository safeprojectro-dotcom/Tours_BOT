"""B15B: read-only publishing console queue — aggregates review-package + tour reads; no I/O side effects."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle, TourStatus
from app.repositories.supplier import SupplierOfferRepository
from app.repositories.tour import TourRepository
from app.schemas.admin_publishing_console import (
    AdminPublishingConsoleItemRead,
    AdminPublishingConsoleOfferDebugRead,
    AdminPublishingConsoleRead,
    AdminPublishingConsoleTourDebugRead,
    PublishingConsoleCandidateKind,
    PublishingConsoleItemStatus,
)
from app.schemas.supplier_admin import AdminSupplierOfferReviewPackageRead
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.supplier_offer_review_package_service import SupplierOfferReviewPackageService


PublishingConsoleKindQuery = Literal[
    "supplier_offer_initial",
    "tour_promotion",
    "ready",
    "blocked",
    "needs_attention",
]


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _publish_showcase_enabled(rp: AdminSupplierOfferReviewPackageRead) -> bool:
    for a in rp.operator_workflow.actions:
        if a.code == "publish_showcase_channel" and a.enabled:
            return True
    return False


def _classify_supplier_offer(
    rp: AdminSupplierOfferReviewPackageRead,
) -> PublishingConsoleItemStatus:
    life = rp.offer.lifecycle_status
    if life == SupplierOfferLifecycle.REJECTED:
        return "blocked"
    ai = rp.ai_public_copy_review
    if ai is not None and ai.ai_block_present and not ai.fact_lock_passed:
        return "blocked"
    if _publish_showcase_enabled(rp):
        return "ready"
    return "needs_attention"


def _blocked_reasons_offer(
    rp: AdminSupplierOfferReviewPackageRead,
    status: PublishingConsoleItemStatus,
) -> list[str]:
    out: list[str] = []
    out.extend(rp.operator_workflow.blocking_reasons or [])
    if rp.offer.lifecycle_status == SupplierOfferLifecycle.REJECTED:
        out.append("Offer lifecycle is rejected.")
    ai = rp.ai_public_copy_review
    if ai is not None and ai.ai_block_present and not ai.fact_lock_passed:
        out.extend(["AI fact lock: " + x for x in (ai.blocking_issues or [])])
    if status == "blocked" and not out:
        out.append("Not ready for channel publish; see review-package warnings.")
    return out[:12]


def _target_summary_offer(rp: AdminSupplierOfferReviewPackageRead) -> str:
    parts: list[str] = [f"supplier_offer #{rp.offer.id}"]
    lc = rp.linked_tour_catalog
    if lc is not None and (lc.tour_code or "").strip():
        parts.append(f"tour_code {lc.tour_code.strip()}")
    eff = rp.showcase_template_preview.effective_template_id
    if eff:
        parts.append(f"template {eff}")
    return " · ".join(parts)


def _human_summary_offer(rp: AdminSupplierOfferReviewPackageRead, status: PublishingConsoleItemStatus) -> str:
    step = (rp.conversion_closure.next_missing_step or "").strip()
    pna = (rp.operator_workflow.primary_next_action or "").strip()
    if status == "ready":
        return "Showcase channel publish is enabled in operator workflow when you choose to send."
    if step:
        return f"Conversion chain: next gate `{step}`."
    if pna:
        return f"Primary workflow action: `{pna}`."
    return "Review supplier offer packaging, moderation, and bridge steps before channel publish."


def _classify_tour(
    *,
    tour_status: TourStatus,
    departure: datetime,
    catalog_visible: bool,
    seats_available: int,
    now: datetime,
) -> PublishingConsoleItemStatus:
    if tour_status != TourStatus.OPEN_FOR_SALE:
        return "blocked"
    dep = departure if departure.tzinfo else departure.replace(tzinfo=UTC)
    if dep.astimezone(UTC) < now:
        return "blocked"
    if not catalog_visible:
        return "needs_attention"
    if seats_available < 1:
        return "blocked"
    return "ready"


def _blocked_reasons_tour(
    *,
    status: TourStatus,
    departure: datetime,
    catalog_visible: bool,
    seats_available: int,
    now: datetime,
) -> list[str]:
    reasons: list[str] = []
    if status != TourStatus.OPEN_FOR_SALE:
        reasons.append(f"Tour status is {status.value}; expected open_for_sale for catalog promotion.")
    dep = departure if departure.tzinfo else departure.replace(tzinfo=UTC)
    if dep.astimezone(UTC) < now:
        reasons.append("Departure is in the past.")
    if not catalog_visible:
        reasons.append("Tour is not in the customer catalog time window (departure / sales_deadline).")
    if seats_available < 1:
        reasons.append("No seats available; not suitable for promotion / last-seats posts.")
    return reasons


class AdminPublishingConsoleService:
    """Builds a merged, sorted candidate list for the publishing console (read-only)."""

    def __init__(
        self,
        *,
        offers: SupplierOfferRepository | None = None,
        tours: TourRepository | None = None,
        review_pkg: SupplierOfferReviewPackageService | None = None,
    ) -> None:
        self._offers = offers or SupplierOfferRepository()
        self._tours = tours or TourRepository()
        self._review = review_pkg or SupplierOfferReviewPackageService()

    def read_console(
        self,
        session: Session,
        *,
        limit: int = 20,
        kind: PublishingConsoleKindQuery | None = None,
    ) -> AdminPublishingConsoleRead:
        """Return up to ``limit`` items. ``kind`` narrows source or status per B15B query contract."""
        source: PublishingConsoleCandidateKind | None
        status_filter: PublishingConsoleItemStatus | None
        source, status_filter = _normalize_kind(kind)

        offer_budget, tour_budget = _budgets(limit, source)
        items: list[AdminPublishingConsoleItemRead] = []

        if source in (None, "supplier_offer_initial"):
            items.extend(self._supplier_offer_items(session, max_items=offer_budget))

        if source in (None, "tour_promotion"):
            items.extend(
                self._tour_promotion_items(
                    session,
                    max_items=tour_budget,
                    now=_now_utc(),
                ),
            )

        if status_filter is not None:
            items = [i for i in items if i.console_status == status_filter]

        items = _sort_console_items(items)
        trimmed = items[:limit]

        return AdminPublishingConsoleRead(
            items=trimmed,
            total_returned=len(trimmed),
            query_debug={
                "limit": limit,
                "kind": kind,
                "normalized_source": source,
                "normalized_status_filter": status_filter,
            },
        )

    def _supplier_offer_items(
        self,
        session: Session,
        *,
        max_items: int,
    ) -> list[AdminPublishingConsoleItemRead]:
        if max_items < 1:
            return []
        scan = min(40, max(max_items * 3, 12))
        rows = self._offers.list_for_admin(session, lifecycle_status=None, limit=scan, offset=0)
        out: list[AdminPublishingConsoleItemRead] = []
        for row in rows:
            rp = self._review.review_package(session, offer_id=row.id)
            if row.lifecycle_status == SupplierOfferLifecycle.PUBLISHED and rp.conversion_closure.next_missing_step is None:
                continue
            status = _classify_supplier_offer(rp)
            br = _blocked_reasons_offer(rp, status)
            item = AdminPublishingConsoleItemRead(
                candidate_key=f"supplier_offer:{row.id}",
                kind="supplier_offer_initial",
                console_status=status,
                title=(row.title or f"Offer #{row.id}").strip() or f"Offer #{row.id}",
                subtitle=f"Lifecycle {row.lifecycle_status}",
                target_summary=_target_summary_offer(rp),
                next_best_action=rp.operator_workflow.primary_next_action or (
                    rp.recommended_next_actions[0] if rp.recommended_next_actions else None
                ),
                blocked_reasons=br,
                human_summary=_human_summary_offer(rp, status),
                review_package_path=f"/admin/supplier-offers/{row.id}/review-package",
                admin_tour_path=None,
                offer_debug=AdminPublishingConsoleOfferDebugRead(
                    supplier_offer_id=row.id,
                    lifecycle_status=row.lifecycle_status,
                    packaging_status=row.packaging_status,
                    can_publish_now=rp.showcase_preview.can_publish_now,
                    next_missing_step=rp.conversion_closure.next_missing_step,
                    effective_showcase_template_id=rp.showcase_template_preview.effective_template_id,
                    primary_operator_action=rp.operator_workflow.primary_next_action,
                ),
                tour_debug=None,
            )
            out.append(item)
        return out[:max_items]


    def _tour_promotion_items(
        self,
        session: Session,
        *,
        max_items: int,
        now: datetime,
    ) -> list[AdminPublishingConsoleItemRead]:
        if max_items < 1:
            return []
        rows = self._tours.list_by_departure_desc(
            session,
            limit=min(80, max_items * 4),
            offset=0,
            status=TourStatus.OPEN_FOR_SALE,
        )
        enriched: list[tuple[datetime, AdminPublishingConsoleItemRead]] = []
        for t in rows:
            catalog_visible = tour_is_customer_catalog_visible(
                departure_datetime=t.departure_datetime,
                sales_deadline=t.sales_deadline,
                now=now,
            )
            status = _classify_tour(
                tour_status=t.status,
                departure=t.departure_datetime,
                catalog_visible=catalog_visible,
                seats_available=t.seats_available,
                now=now,
            )
            br = _blocked_reasons_tour(
                status=t.status,
                departure=t.departure_datetime,
                catalog_visible=catalog_visible,
                seats_available=t.seats_available,
                now=now,
            )
            human = (
                "Candidate for tour promotion / last-seats style posts (B15B does not send)."
                if status == "ready"
                else "Not ideal for catalog promotion until gates pass."
            )
            enriched.append(
                (
                    t.departure_datetime,
                    AdminPublishingConsoleItemRead(
                        candidate_key=f"tour:{t.id}",
                        kind="tour_promotion",
                        console_status=status,
                        title=(t.title_default or t.code or f"Tour #{t.id}").strip(),
                        subtitle=f"{t.code} · {t.sales_mode.value}",
                        target_summary=f"exact_tour · /mini-app/tours/{t.code} (conceptual; B15D template)",
                        next_best_action="compose_tour_promotion_draft" if status == "ready" else "resolve_tour_blockers",
                        blocked_reasons=br,
                        human_summary=human,
                        review_package_path=None,
                        admin_tour_path=f"/admin/tours/{t.id}",
                        offer_debug=None,
                        tour_debug=AdminPublishingConsoleTourDebugRead(
                            tour_id=t.id,
                            tour_code=t.code,
                            tour_status=t.status.value,
                            sales_mode=t.sales_mode.value,
                            seats_available=t.seats_available,
                            seats_total=t.seats_total,
                            catalog_customer_visible=catalog_visible,
                        ),
                    ),
                ),
            )
        enriched.sort(
            key=lambda pair: (
                _STATUS_ORDER.get(pair[1].console_status, 9),
                pair[0] if pair[0].tzinfo else pair[0].replace(tzinfo=UTC),
            ),
        )
        return [pair[1] for pair in enriched[:max_items]]


def _normalize_kind(
    kind: PublishingConsoleKindQuery | None,
) -> tuple[PublishingConsoleCandidateKind | None, PublishingConsoleItemStatus | None]:
    if kind is None:
        return None, None
    if kind == "supplier_offer_initial":
        return "supplier_offer_initial", None
    if kind == "tour_promotion":
        return "tour_promotion", None
    if kind in ("ready", "blocked", "needs_attention"):
        return None, kind
    return None, None


def _budgets(
    limit: int,
    source: PublishingConsoleCandidateKind | None,
) -> tuple[int, int]:
    if source == "supplier_offer_initial":
        return limit, 0
    if source == "tour_promotion":
        return 0, limit
    half = max(1, limit // 2)
    rest = limit - half
    return half, rest


_STATUS_ORDER = {"ready": 0, "needs_attention": 1, "blocked": 2}


def _sort_console_items(items: list[AdminPublishingConsoleItemRead]) -> list[AdminPublishingConsoleItemRead]:
    return sorted(
        items,
        key=lambda i: (_STATUS_ORDER.get(i.console_status, 9), i.kind, i.candidate_key),
    )
