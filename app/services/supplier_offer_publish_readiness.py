"""B15H: derive read-only publish readiness from review-package read model only (no I/O, no mutations)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus
from app.schemas.admin_publish_readiness import (
    AdminPublishReadinessGateRead,
    AdminPublishReadinessRead,
    PublishReadinessBadge,
    PublishReadinessSummaryStatus,
)
from app.schemas.supplier_admin import AdminSupplierOfferReviewPackageRead
from app.services.admin_navigation_paths import (
    supplier_offer_prepare_conversion_chain_plan_path,
    supplier_offer_publish_showcase_path,
)
from app.services.supplier_offer_cover_media_quality_review import cover_media_publish_blocking_reasons
from app.services.supplier_offer_publish_safe_vnext import PublishSafeVNextStatus


@dataclass(frozen=True, slots=True)
class _PublishReadinessUxParts:
    summary: str
    badge: PublishReadinessBadge
    next_action_code: str | None
    next_action_label: str | None
    primary_blocker: str | None
    warning_summary: str | None
    gate_summary: str


def _compute_publish_readiness_ux(
    *,
    status: PublishReadinessSummaryStatus,
    gates: list[AdminPublishReadinessGateRead],
    gates_passed_count: int,
    gates_failed_count: int,
    gates_warning_count: int,
    recommended_action: str,
) -> _PublishReadinessUxParts:
    """B15I — compact fields derived from status + gate list (read-only, no I/O)."""

    na_n = sum(1 for g in gates if g.status == "not_applicable")
    gate_summary = (
        f"{gates_passed_count} passed · {gates_failed_count} failed · "
        f"{gates_warning_count} warnings · {na_n} not applicable"
    )

    blocker_reasons = [
        (g.reason or g.label or g.code)
        for g in gates
        if g.status == "failed" and g.severity == "blocker"
    ]
    primary_blocker = blocker_reasons[0] if blocker_reasons else None

    warn_codes = [g.code for g in gates if g.status == "warning"]
    warning_summary: str | None
    if not warn_codes:
        warning_summary = None
    elif len(warn_codes) <= 4:
        warning_summary = f"{len(warn_codes)} warning(s): " + ", ".join(warn_codes)
    else:
        warning_summary = f"{len(warn_codes)} warning(s): " + ", ".join(warn_codes[:4]) + ", …"

    badge: PublishReadinessBadge = status

    if status == "already_published":
        summary = "Already published — not a candidate for first-time publish suggestion."
        next_action_code = "review_conversion_health"
        next_action_label = "Review conversion health on review-package (avoid duplicate showcase without ops review)."
    elif status == "ready_to_suggest":
        summary = "All blocking gates pass — ready to suggest manual showcase publish."
        next_action_code = "manual_publish_available"
        next_action_label = "Manual showcase publish available — operator confirms, then POST publish."
    elif status == "needs_review":
        summary = "Non-blocking warnings remain — review before suggesting manual publish."
        next_action_code = "review_warnings"
        next_action_label = "Review warning gates and operator workflow before manual publish."
    elif status == "not_applicable":
        summary = (recommended_action[:240] + "…") if len(recommended_action) > 240 else recommended_action
        next_action_code = "not_applicable"
        next_action_label = None
    else:  # blocked
        tail = primary_blocker or recommended_action
        summary = f"Blocked — {tail}" if tail else "Blocked — resolve prerequisites before publish suggestion."
        next_action_code = "resolve_publish_blockers"
        next_action_label = "Resolve blocking gates (see primary_blocker and recommended_action)."

    return _PublishReadinessUxParts(
        summary=summary,
        badge=badge,
        next_action_code=next_action_code,
        next_action_label=next_action_label,
        primary_blocker=primary_blocker,
        warning_summary=warning_summary,
        gate_summary=gate_summary,
    )


def _finalize_publish_readiness(
    *,
    status: PublishReadinessSummaryStatus,
    recommended_action: str,
    gates_passed_count: int,
    gates_failed_count: int,
    gates_warning_count: int,
    gates: list[AdminPublishReadinessGateRead],
    can_suggest_manual_publish: bool,
    publish_action_path: str | None,
    prepare_conversion_chain_plan_path: str | None,
    generated_at: datetime,
) -> AdminPublishReadinessRead:
    ux = _compute_publish_readiness_ux(
        status=status,
        gates=gates,
        gates_passed_count=gates_passed_count,
        gates_failed_count=gates_failed_count,
        gates_warning_count=gates_warning_count,
        recommended_action=recommended_action,
    )
    return AdminPublishReadinessRead(
        status=status,
        recommended_action=recommended_action,
        gates_passed_count=gates_passed_count,
        gates_failed_count=gates_failed_count,
        gates_warning_count=gates_warning_count,
        gates=gates,
        can_suggest_manual_publish=can_suggest_manual_publish,
        publish_action_path=publish_action_path,
        prepare_conversion_chain_plan_path=prepare_conversion_chain_plan_path,
        generated_at=generated_at,
        summary=ux.summary,
        badge=ux.badge,
        next_action_code=ux.next_action_code,
        next_action_label=ux.next_action_label,
        primary_blocker=ux.primary_blocker,
        warning_summary=ux.warning_summary,
        gate_summary=ux.gate_summary,
    )


def _publish_safe_status_from_draft(packaging_draft_json: object) -> str | None:
    if not isinstance(packaging_draft_json, dict):
        return None
    block = packaging_draft_json.get("publish_safe")
    if not isinstance(block, dict):
        return None
    st = block.get("status")
    return st if isinstance(st, str) else None


def stub_publish_readiness_placeholder(*, offer_id: int, generated_at: datetime) -> AdminPublishReadinessRead:
    """Placeholder until review-package finishes aggregation (replaced before return)."""

    return _finalize_publish_readiness(
        status="blocked",
        recommended_action="Recomputing publish readiness…",
        gates_passed_count=0,
        gates_failed_count=0,
        gates_warning_count=0,
        gates=[
            AdminPublishReadinessGateRead(
                code="pending",
                label="Readiness",
                status="not_applicable",
                reason="Placeholder — replaced after review-package assembly.",
                severity="info",
            ),
        ],
        can_suggest_manual_publish=False,
        publish_action_path=supplier_offer_publish_showcase_path(offer_id),
        prepare_conversion_chain_plan_path=supplier_offer_prepare_conversion_chain_plan_path(offer_id),
        generated_at=generated_at,
    )


def publish_readiness_for_tour_promotion(*, generated_at: datetime) -> AdminPublishReadinessRead:
    """Publishing-console tour-promotion rows are not supplier-offer showcase candidates."""

    return _finalize_publish_readiness(
        status="not_applicable",
        recommended_action="Tour promotion rows are not evaluated for supplier-offer showcase publish readiness.",
        gates_passed_count=0,
        gates_failed_count=0,
        gates_warning_count=0,
        gates=[
            AdminPublishReadinessGateRead(
                code="candidate_kind",
                label="Console candidate",
                status="not_applicable",
                reason="Row is tour_promotion, not supplier_offer_initial.",
                severity="info",
            ),
        ],
        can_suggest_manual_publish=False,
        publish_action_path=None,
        prepare_conversion_chain_plan_path=None,
        generated_at=generated_at,
    )


def derive_supplier_offer_publish_readiness(
    pkg: AdminSupplierOfferReviewPackageRead,
    *,
    generated_at: datetime | None = None,
) -> AdminPublishReadinessRead:
    """Evaluate suggest-only publish readiness from an existing review-package snapshot."""

    t = generated_at or datetime.now(UTC)
    offer = pkg.offer
    offer_id = offer.id
    plan_path = supplier_offer_prepare_conversion_chain_plan_path(offer_id)
    publish_path = supplier_offer_publish_showcase_path(offer_id)

    gates: list[AdminPublishReadinessGateRead] = []

    # --- lifecycle (first-time publish suggestion; published offers are terminal for suggestion)
    lc = offer.lifecycle_status
    if lc is SupplierOfferLifecycle.PUBLISHED:
        gates.append(
            AdminPublishReadinessGateRead(
                code="lifecycle",
                label="Offer lifecycle",
                status="not_applicable",
                reason="Offer is already published; do not suggest duplicate initial showcase publish from this funnel.",
                severity="info",
            ),
        )
    elif lc is SupplierOfferLifecycle.REJECTED:
        gates.append(
            AdminPublishReadinessGateRead(
                code="lifecycle",
                label="Offer lifecycle",
                status="failed",
                reason="Moderation rejected; resolve before any publish suggestion.",
                severity="blocker",
            ),
        )
    elif lc is SupplierOfferLifecycle.APPROVED:
        gates.append(
            AdminPublishReadinessGateRead(
                code="lifecycle",
                label="Offer lifecycle",
                status="passed",
                reason="Moderation approved.",
                severity="info",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="lifecycle",
                label="Offer lifecycle",
                status="failed",
                reason=f"Lifecycle must be approved for showcase publish (current: {lc.value}).",
                severity="blocker",
            ),
        )

    # --- packaging
    pk = offer.packaging_status
    if pk is SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH:
        gates.append(
            AdminPublishReadinessGateRead(
                code="packaging",
                label="Packaging approval",
                status="passed",
                reason="approved_for_publish",
                severity="info",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="packaging",
                label="Packaging approval",
                status="failed",
                reason=f"packaging_status must be approved_for_publish (current: {pk.value}).",
                severity="blocker",
            ),
        )

    # --- required offer fields for bridge
    missing = pkg.bridge_readiness.missing_fields
    if missing:
        gates.append(
            AdminPublishReadinessGateRead(
                code="offer_fields",
                label="Required offer fields",
                status="failed",
                reason="Missing: " + ", ".join(missing[:8]) + ("…" if len(missing) > 8 else ""),
                severity="blocker",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="offer_fields",
                label="Required offer fields",
                status="passed",
                severity="info",
            ),
        )

    # --- AI public copy / fact lock (blocking issues only)
    ai = pkg.ai_public_copy_review
    if ai.blocking_issues or (ai.ai_block_present and not ai.fact_lock_passed):
        detail = "; ".join(ai.blocking_issues[:3]) if ai.blocking_issues else "Fact lock did not pass"
        gates.append(
            AdminPublishReadinessGateRead(
                code="ai_public_copy",
                label="AI public copy / fact lock",
                status="failed",
                reason=detail,
                severity="blocker",
            ),
        )
    elif ai.warnings:
        gates.append(
            AdminPublishReadinessGateRead(
                code="ai_public_copy",
                label="AI public copy / fact lock",
                status="warning",
                reason="Non-blocking warnings present; review before publish.",
                severity="warning",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="ai_public_copy",
                label="AI public copy / fact lock",
                status="passed",
                severity="info",
            ),
        )

    # --- content quality (warnings only in current model)
    cq = pkg.content_quality_review
    if cq.has_quality_warnings:
        gates.append(
            AdminPublishReadinessGateRead(
                code="content_quality",
                label="Content quality",
                status="warning",
                reason="Deterministic copy/discount warnings present (admin review recommended).",
                severity="warning",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="content_quality",
                label="Content quality",
                status="passed",
                severity="info",
            ),
        )

    # --- media / channel card (same signals as publish_showcase operator_workflow)
    media_blocks = cover_media_publish_blocking_reasons(
        cover_media_quality_review=pkg.cover_media_quality_review,
        publication_mode=pkg.showcase_preview.publication_mode,
    )
    if media_blocks:
        gates.append(
            AdminPublishReadinessGateRead(
                code="showcase_media",
                label="Showcase media",
                status="failed",
                reason="; ".join(media_blocks[:4]),
                severity="blocker",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="showcase_media",
                label="Showcase media",
                status="passed",
                reason=f"publication_mode={pkg.showcase_preview.publication_mode}",
                severity="info",
            ),
        )

    # --- publish_safe metadata (deferred pipeline is warning, not auto-blocker)
    ps = _publish_safe_status_from_draft(offer.packaging_draft_json)
    if ps is None:
        gates.append(
            AdminPublishReadinessGateRead(
                code="publish_safe",
                label="Publish-safe metadata",
                status="not_applicable",
                reason="No publish_safe block in packaging_draft_json (metadata-only policy may still allow text-only).",
                severity="info",
            ),
        )
    elif ps in (PublishSafeVNextStatus.FAILED.value, PublishSafeVNextStatus.BLOCKED.value):
        gates.append(
            AdminPublishReadinessGateRead(
                code="publish_safe",
                label="Publish-safe metadata",
                status="failed",
                reason=f"publish_safe.status is {ps!r}.",
                severity="blocker",
            ),
        )
    elif ps in (PublishSafeVNextStatus.DEFERRED.value, PublishSafeVNextStatus.PENDING.value):
        gates.append(
            AdminPublishReadinessGateRead(
                code="publish_safe",
                label="Publish-safe metadata",
                status="warning",
                reason="Durable publish-safe asset pipeline not complete; channel policy may still allow showcase.",
                severity="warning",
            ),
        )
    elif ps == PublishSafeVNextStatus.READY.value:
        gates.append(
            AdminPublishReadinessGateRead(
                code="publish_safe",
                label="Publish-safe metadata",
                status="passed",
                reason="publish_safe ready (metadata).",
                severity="info",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="publish_safe",
                label="Publish-safe metadata",
                status="warning",
                reason=f"Unknown publish_safe.status {ps!r}.",
                severity="warning",
            ),
        )

    # --- showcase preview / can_publish_now (aggregated channel gating)
    if pkg.showcase_preview.can_publish_now:
        gates.append(
            AdminPublishReadinessGateRead(
                code="showcase_preview",
                label="Showcase preview",
                status="passed",
                reason="can_publish_now is true for preview payload.",
                severity="info",
            ),
        )
    else:
        hint = pkg.showcase_preview.warnings[0] if pkg.showcase_preview.warnings else "can_publish_now is false"
        gates.append(
            AdminPublishReadinessGateRead(
                code="showcase_preview",
                label="Showcase preview",
                status="failed",
                reason=hint,
                severity="blocker",
            ),
        )

    # --- prepare_conversion_chain plan (internal readiness; correlates with B15G)
    pcs = pkg.prepare_conversion_chain_plan_status
    if pcs == "already_prepared":
        gates.append(
            AdminPublishReadinessGateRead(
                code="prepare_conversion_chain",
                label="Prepare conversion chain",
                status="passed",
                reason="Internal bridge/catalog/execution chain satisfied.",
                severity="info",
            ),
        )
    elif pcs == "partial":
        gates.append(
            AdminPublishReadinessGateRead(
                code="prepare_conversion_chain",
                label="Prepare conversion chain",
                status="warning",
                reason="Internal preparation chain still has pending steps.",
                severity="warning",
            ),
        )
    elif pcs in ("ineligible", "blocked"):
        gates.append(
            AdminPublishReadinessGateRead(
                code="prepare_conversion_chain",
                label="Prepare conversion chain",
                status="failed",
                reason=f"Plan status {pcs!r} (blockers_count={pkg.prepare_conversion_chain_blockers_count}).",
                severity="blocker",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="prepare_conversion_chain",
                label="Prepare conversion chain",
                status="failed",
                reason=f"Unexpected plan status {pcs!r}.",
                severity="blocker",
            ),
        )

    # --- tour bridge
    if pkg.active_tour_bridge is not None:
        gates.append(
            AdminPublishReadinessGateRead(
                code="tour_bridge",
                label="Tour bridge",
                status="passed",
                reason="Active tour bridge present.",
                severity="info",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="tour_bridge",
                label="Tour bridge",
                status="failed",
                reason="No active tour bridge.",
                severity="blocker",
            ),
        )

    # --- catalog listing (Mini App)
    catalog = pkg.linked_tour_catalog
    if catalog is None:
        gates.append(
            AdminPublishReadinessGateRead(
                code="catalog_listing",
                label="Catalog listing",
                status="failed",
                reason="Linked tour catalog preview unavailable.",
                severity="blocker",
            ),
        )
    elif catalog.b8_same_offer_date_conflict:
        gates.append(
            AdminPublishReadinessGateRead(
                code="catalog_listing",
                label="Catalog listing",
                status="failed",
                reason="B8 same-offer date conflict blocks catalog activation.",
                severity="blocker",
            ),
        )
    elif catalog.catalog_listed_for_mini_app:
        gates.append(
            AdminPublishReadinessGateRead(
                code="catalog_listing",
                label="Catalog listing",
                status="passed",
                reason="Tour listed for Mini App catalog.",
                severity="info",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="catalog_listing",
                label="Catalog listing",
                status="failed",
                reason="Tour not listed for Mini App catalog (activate when eligible).",
                severity="blocker",
            ),
        )

    # --- execution link (B15C: required before channel publish when gates pass)
    ex = pkg.execution_links_review
    if ex.active_link is not None:
        gates.append(
            AdminPublishReadinessGateRead(
                code="execution_link",
                label="Execution link",
                status="passed",
                reason="Active execution link present.",
                severity="info",
            ),
        )
    else:
        gates.append(
            AdminPublishReadinessGateRead(
                code="execution_link",
                label="Execution link",
                status="failed",
                reason="No active execution link (exact-tour CTA requires it).",
                severity="blocker",
            ),
        )

    passed_n = sum(1 for g in gates if g.status == "passed")
    failed_n = sum(1 for g in gates if g.status == "failed")
    warn_n = sum(1 for g in gates if g.status == "warning")

    has_blocker_failed = any(g.status == "failed" and g.severity == "blocker" for g in gates)
    has_warning = any(g.status == "warning" for g in gates)

    # Operator workflow publish affordance mirrors product policy for manual publish
    pub_action = next(
        (a for a in pkg.operator_workflow.actions if a.code == "publish_showcase_channel"),
        None,
    )

    if lc is SupplierOfferLifecycle.PUBLISHED:
        return _finalize_publish_readiness(
            status="already_published",
            recommended_action=(
                "Offer is already published. Use review-package for conversion health; "
                "avoid duplicate showcase publish without explicit ops review."
            ),
            gates_passed_count=passed_n,
            gates_failed_count=failed_n,
            gates_warning_count=warn_n,
            gates=gates,
            can_suggest_manual_publish=False,
            publish_action_path=None,
            prepare_conversion_chain_plan_path=plan_path,
            generated_at=t,
        )

    if has_blocker_failed:
        reason = next((g.reason for g in gates if g.status == "failed"), None)
        ra = pkg.operator_workflow.primary_next_action or reason or "Resolve blocking gates before manual publish."
        return _finalize_publish_readiness(
            status="blocked",
            recommended_action=ra,
            gates_passed_count=passed_n,
            gates_failed_count=failed_n,
            gates_warning_count=warn_n,
            gates=gates,
            can_suggest_manual_publish=False,
            publish_action_path=publish_path,
            prepare_conversion_chain_plan_path=plan_path,
            generated_at=t,
        )

    if has_warning:
        return _finalize_publish_readiness(
            status="needs_review",
            recommended_action=(
                "Non-blocking warnings remain; review operator_workflow and gates before suggesting manual publish."
            ),
            gates_passed_count=passed_n,
            gates_failed_count=failed_n,
            gates_warning_count=warn_n,
            gates=gates,
            can_suggest_manual_publish=False,
            publish_action_path=publish_path,
            prepare_conversion_chain_plan_path=plan_path,
            generated_at=t,
        )

    # Strict ready: publish action must be enabled in workflow (final product check)
    if pub_action is not None and pub_action.enabled:
        return _finalize_publish_readiness(
            status="ready_to_suggest",
            recommended_action=(
                "Readiness gates pass; operator may execute manual showcase publish (POST) after explicit confirmation."
            ),
            gates_passed_count=passed_n,
            gates_failed_count=failed_n,
            gates_warning_count=warn_n,
            gates=gates,
            can_suggest_manual_publish=True,
            publish_action_path=publish_path,
            prepare_conversion_chain_plan_path=plan_path,
            generated_at=t,
        )

    return _finalize_publish_readiness(
        status="blocked",
        recommended_action=pub_action.disabled_reason if pub_action and pub_action.disabled_reason else "Publish affordance disabled; refresh review-package.",
        gates_passed_count=passed_n,
        gates_failed_count=failed_n,
        gates_warning_count=warn_n,
        gates=gates,
        can_suggest_manual_publish=False,
        publish_action_path=publish_path,
        prepare_conversion_chain_plan_path=plan_path,
        generated_at=t,
    )


__all__ = [
    "derive_supplier_offer_publish_readiness",
    "publish_readiness_for_tour_promotion",
    "stub_publish_readiness_placeholder",
]
