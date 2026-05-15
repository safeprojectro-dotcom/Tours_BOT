"""B15B/B15D/B15E/B15F: read-only publishing console — review-package + tours + readiness + affordances + template/channel read model; no I/O side effects."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, cast

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import SupplierOfferLifecycle, SupplierOfferPaymentMode, TourStatus
from app.repositories.supplier import SupplierOfferRepository
from app.repositories.tour import TourRepository
from app.schemas.admin_publishing_console import (
    AdminPublishingConsoleActionAffordanceRead,
    AdminPublishingConsoleFutureCapabilityHintRead,
    AdminPublishingConsoleItemRead,
    AdminPublishingConsoleOfferDebugRead,
    AdminPublishingConsolePreviewRead,
    AdminPublishingConsoleRead,
    AdminPublishingConsoleTemplateLibraryEntryRead,
    AdminPublishingConsoleTemplateLibraryRead,
    AdminPublishingConsoleTourDebugRead,
    PublishingConsoleActionDangerLevel,
    PublishingConsoleCandidateKind,
    PublishingConsoleChannelKind,
    PublishingConsoleChannelStatus,
    PublishingConsoleConversionTargetKind,
    PublishingConsoleCtaSafetyStatusLiteral,
    PublishingConsoleItemStatus,
    PublishingConsoleMediaPolicyStatus,
    PublishingConsolePreviewStatus,
    PublishingConsoleReadinessLevel,
    PublishingConsoleTemplateFamily,
    PublishingConsoleTemplateKind,
    PublishingConsoleTemplateLibraryEntryStatus,
    PublishingConsoleTemplateLibraryFamily,
    PublishingConsoleTemplateSourceStatus,
)
from app.schemas.supplier_admin import AdminSupplierOfferReviewPackageRead
from app.services.admin_navigation_paths import supplier_offer_prepare_conversion_chain_plan_path
from app.services.customer_catalog_visibility import tour_is_customer_catalog_visible
from app.services.supplier_offer_channel_publish_gate import channel_publish_exact_tour_ready
from app.services.supplier_offer_cover_media_quality_review import cover_media_publish_blocking_reasons
from app.services.supplier_offer_deep_link import (
    mini_app_supplier_offer_url,
    mini_app_tour_channel_startapp_url,
    mini_app_tour_detail_url,
    normalize_telegram_mini_app_short_name_for_url,
)
from app.services.supplier_offer_publish_readiness import publish_readiness_for_tour_promotion
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


def _readiness_level_from_console(status: PublishingConsoleItemStatus) -> PublishingConsoleReadinessLevel:
    if status == "ready":
        return "ready"
    if status == "needs_attention":
        return "needs_action"
    if status == "blocked":
        return "blocked"
    return "unknown"


def _blocker_codes_from_b15c_reasons(reasons: list[str]) -> list[str]:
    codes: list[str] = []
    for r in reasons:
        low = r.lower()
        if "execution link" in low or "execution_link" in low:
            codes.append("missing_execution_link")
        elif "catalog-listed" in low or "catalog listed" in low:
            codes.append("tour_not_listed")
        elif "open_for_sale" in low:
            codes.append("tour_not_listed")
        elif "bridge" in low:
            codes.append("bridge_mismatch")
        elif "tour_code" in low or "tour code" in low:
            codes.append("missing_tour_code")
        elif "departure" in low:
            codes.append("tour_departure_invalid")
    seen: set[str] = set()
    out: list[str] = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:12]


def _conversion_url_for_tour_code(settings: object, tour_code: str) -> str | None:
    tc = (tour_code or "").strip()
    if not tc:
        return None
    uname = (getattr(settings, "telegram_bot_username", None) or "").strip().lstrip("@")
    if uname and "/" not in uname:
        try:
            sn = normalize_telegram_mini_app_short_name_for_url(
                getattr(settings, "telegram_mini_app_short_name", None)
            )
            return mini_app_tour_channel_startapp_url(
                bot_username=uname,
                tour_code=tc,
                mini_app_short_name=sn,
            )
        except ValueError:
            pass
    base = (getattr(settings, "telegram_mini_app_url", None) or "").strip().rstrip("/")
    if base:
        try:
            return mini_app_tour_detail_url(mini_app_url=base, tour_code=tc)
        except ValueError:
            return None
    return None


def _next_action_fields(
    rp: AdminSupplierOfferReviewPackageRead, offer_id: int
) -> tuple[str | None, str | None, str | None]:
    pna = (rp.operator_workflow.primary_next_action or "").strip() or None
    code_match: str | None = None
    label_match: str | None = None
    endpoint_match: str | None = None
    for a in rp.operator_workflow.actions:
        if not a.enabled:
            continue
        if pna and a.code == pna:
            code_match, label_match = a.code, a.label
            endpoint_match = a.endpoint.replace("{offer_id}", str(offer_id))
            break
    if code_match is None:
        for a in rp.operator_workflow.actions:
            if a.enabled and a.danger_level in ("conversion_enabling", "public_dangerous"):
                code_match, label_match = a.code, a.label
                endpoint_match = a.endpoint.replace("{offer_id}", str(offer_id))
                break
    return code_match, label_match, endpoint_match


def _b15d_supplier_offer(
    session: Session,
    *,
    offer_id: int,
    rp: AdminSupplierOfferReviewPackageRead,
    console_status: PublishingConsoleItemStatus,
    blocked_reasons: list[str],
) -> dict[str, Any]:
    settings = get_settings()
    rl = _readiness_level_from_console(console_status)
    cc = rp.conversion_closure
    lc = rp.linked_tour_catalog
    exact_ok, exact_reasons = channel_publish_exact_tour_ready(session, offer_id=offer_id)
    tour_code = (lc.tour_code or "").strip() if lc else ""

    ctk: PublishingConsoleConversionTargetKind
    conv_url: str | None = None
    base = (settings.telegram_mini_app_url or "").strip().rstrip("/")

    if cc.has_tour_bridge and tour_code:
        ctk = "exact_tour"
        conv_url = _conversion_url_for_tour_code(settings, tour_code)
    elif cc.has_tour_bridge:
        ctk = "exact_tour"
        conv_url = None
    else:
        ctk = "none"
        if base:
            try:
                conv_url = mini_app_supplier_offer_url(mini_app_url=base, offer_id=offer_id)
                ctk = "supplier_offer_landing"
            except ValueError:
                conv_url = None

    cta_status: PublishingConsoleCtaSafetyStatusLiteral
    if exact_ok:
        cta_status = "exact_tour_ready"
    else:
        codes_from_reasons = _blocker_codes_from_b15c_reasons(exact_reasons)
        if "missing_execution_link" in codes_from_reasons:
            cta_status = "missing_execution_link"
        elif "tour_not_listed" in codes_from_reasons:
            cta_status = "tour_not_listed"
        elif not cc.has_active_execution_link:
            cta_status = "missing_execution_link"
        elif lc is not None and not lc.catalog_listed_for_mini_app:
            cta_status = "tour_not_listed"
        else:
            cta_status = "missing_execution_link"

    pub_act = next(
        (a for a in rp.operator_workflow.actions if a.code == "publish_showcase_channel"),
        None,
    )
    if (
        exact_ok
        and not rp.showcase_preview.can_publish_now
        and pub_act
        and not pub_act.enabled
        and pub_act.disabled_reason
    ):
        dr = pub_act.disabled_reason.lower()
        if any(x in dr for x in ("cover", "media", "photo", "c2b8")):
            cta_status = "media_blocked"

    blocker_codes: list[str] = []
    ns = (cc.next_missing_step or "").strip()
    if ns:
        blocker_codes.append(ns)
    blocker_codes.extend(_blocker_codes_from_b15c_reasons(exact_reasons))
    seen2: set[str] = set()
    dedup: list[str] = []
    for c in blocker_codes:
        if c not in seen2:
            seen2.add(c)
            dedup.append(c)
    blocker_codes = dedup[:12]

    primary: str | None = None
    if blocked_reasons:
        primary = blocked_reasons[0]
    elif exact_reasons:
        primary = exact_reasons[0]
    elif not rp.showcase_preview.can_publish_now and rp.showcase_preview.warnings:
        primary = rp.showcase_preview.warnings[0]
    elif ns:
        primary = f"Next conversion step: {ns}"

    lifecycle_v = getattr(rp.offer.lifecycle_status, "value", rp.offer.lifecycle_status)
    packaging_v = getattr(rp.offer.packaging_status, "value", rp.offer.packaging_status)
    readiness_summary = (
        f"lifecycle={lifecycle_v}; packaging={packaging_v}; "
        f"can_publish_now={rp.showcase_preview.can_publish_now}; b15c_exact_tour_ready={exact_ok}"
    )

    n_code, n_label, adm_path = _next_action_fields(rp, offer_id)
    audit_hint = (
        f"Full audit: GET /admin/supplier-offers/{offer_id}/review-package "
        "(conversion_closure, publish attempts, operator_workflow)."
    )

    return {
        "readiness_summary": readiness_summary,
        "readiness_level": rl,
        "conversion_target_kind": ctk,
        "conversion_target_url": conv_url,
        "cta_safety_status": cta_status,
        "primary_blocker": primary,
        "blocker_codes": blocker_codes,
        "next_action_code": n_code,
        "next_action_label": n_label,
        "admin_action_path": adm_path or f"/admin/supplier-offers/{offer_id}/review-package",
        "preview_path": f"/admin/supplier-offers/{offer_id}/showcase-preview",
        "source_status_summary": (
            f"{lifecycle_v} · packaging {packaging_v} · publish_gate={rp.showcase_preview.can_publish_now}"
        ),
        "audit_hint": audit_hint,
    }


def _b15d_tour_promotion(
    *,
    tour_id: int,
    tour_code: str,
    console_status: PublishingConsoleItemStatus,
    blocked_reasons: list[str],
    human_summary: str,
    tour_status: str,
    sales_mode: str,
    seats_available: int,
) -> dict[str, Any]:
    settings = get_settings()
    rl = _readiness_level_from_console(console_status)
    conv_url = _conversion_url_for_tour_code(settings, tour_code)

    if console_status == "ready":
        cta: PublishingConsoleCtaSafetyStatusLiteral = "exact_tour_ready"
    elif any("catalog" in b.lower() or "window" in b.lower() for b in blocked_reasons):
        cta = "tour_not_listed"
    else:
        cta = "not_applicable"

    primary = blocked_reasons[0] if blocked_reasons else None
    codes: list[str] = []
    if seats_available < 1:
        codes.append("no_seats")
    if tour_status.lower() == "closed":
        codes.append("tour_closed")
    if sales_mode.lower() == "request_only":
        codes.append("request_only")

    readiness_summary = (
        f"tour={tour_code} status={tour_status} sales_mode={sales_mode} "
        f"seats={seats_available}; console={console_status}"
    )

    return {
        "readiness_summary": readiness_summary,
        "readiness_level": rl,
        "conversion_target_kind": "exact_tour",
        "conversion_target_url": conv_url,
        "cta_safety_status": cta,
        "primary_blocker": primary,
        "blocker_codes": codes[:12],
        "next_action_code": None,
        "next_action_label": "Open tour in admin" if tour_id else None,
        "admin_action_path": f"/admin/tours/{tour_id}" if tour_id else None,
        "preview_path": None,
        "source_status_summary": human_summary,
        "audit_hint": "Supplier-offer-only CTA gate fields do not apply to tour promotion rows.",
    }


def _affordances_from_operator_workflow(
    rp: AdminSupplierOfferReviewPackageRead,
    offer_id: int,
) -> list[AdminPublishingConsoleActionAffordanceRead]:
    out: list[AdminPublishingConsoleActionAffordanceRead] = []
    for a in rp.operator_workflow.actions:
        dl = cast(PublishingConsoleActionDangerLevel, a.danger_level)
        out.append(
            AdminPublishingConsoleActionAffordanceRead(
                code=a.code,
                label=a.label,
                kind=dl,
                enabled=a.enabled,
                requires_confirmation=a.requires_confirmation,
                danger_level=dl,
                admin_path=a.endpoint.replace("{offer_id}", str(offer_id)),
                method=a.method,
                implemented=True,
                disabled_reason=a.disabled_reason,
                source="operator_workflow",
            )
        )
    return out


def _tour_promotion_action_affordances(*, tour_id: int) -> list[AdminPublishingConsoleActionAffordanceRead]:
    return [
        AdminPublishingConsoleActionAffordanceRead(
            code="open_tour_admin",
            label="Open tour in admin",
            kind="safe_read",
            enabled=True,
            requires_confirmation=False,
            danger_level="safe_read",
            admin_path=f"/admin/tours/{tour_id}",
            method="GET",
            implemented=True,
            disabled_reason=None,
            source="console_read_only",
        ),
        AdminPublishingConsoleActionAffordanceRead(
            code="verify_mini_app_catalog",
            label="Verify Mini App catalog (customer)",
            kind="safe_read",
            enabled=True,
            requires_confirmation=False,
            danger_level="safe_read",
            admin_path="/mini-app/catalog",
            method="GET",
            implemented=True,
            disabled_reason=None,
            source="console_read_only",
        ),
        AdminPublishingConsoleActionAffordanceRead(
            code="compose_tour_promotion_draft",
            label="Compose tour promotion draft",
            kind="safe_read",
            enabled=False,
            requires_confirmation=False,
            danger_level="safe_read",
            admin_path="/admin/publishing-console",
            method="GET",
            implemented=False,
            disabled_reason="Tour promotion drafts are not implemented yet (forward: B15F+).",
            source="future",
        ),
    ]


def _b15f_future_template_channel_hints() -> tuple[
    list[AdminPublishingConsoleFutureCapabilityHintRead],
    list[AdminPublishingConsoleFutureCapabilityHintRead],
]:
    template_actions = [
        AdminPublishingConsoleFutureCapabilityHintRead(
            code="edit_showcase_template",
            label="Edit template",
            implemented=False,
            enabled=False,
            disabled_reason="Template editor is not implemented in B15F.",
        ),
    ]
    channel_actions = [
        AdminPublishingConsoleFutureCapabilityHintRead(
            code="select_channel",
            label="Select channel",
            implemented=False,
            enabled=False,
            disabled_reason="Channel selector is not implemented in B15F.",
        ),
    ]
    return template_actions, channel_actions


def _b15f_supplier_offer(
    *,
    settings: object,
    rp: AdminSupplierOfferReviewPackageRead,
    offer_id: int,
    title: str,
) -> dict[str, Any]:
    st = rp.showcase_template_preview
    sp = rp.showcase_preview
    cm = rp.cover_media_quality_review
    channel_id = (getattr(settings, "telegram_offer_showcase_channel_id", None) or "").strip()
    channel_configured = bool(channel_id)

    blocking = cover_media_publish_blocking_reasons(
        cover_media_quality_review=cm,
        publication_mode=sp.publication_mode,
    )
    if blocking:
        media_status = cast(PublishingConsoleMediaPolicyStatus, "media_blocked")
        media_summary = blocking[0]
    elif cm.has_warnings and cm.warnings:
        media_status = cast(PublishingConsoleMediaPolicyStatus, "media_review_pending")
        media_summary = cm.warnings[0].message
    elif sp.publication_mode == "text_only":
        media_status = cast(PublishingConsoleMediaPolicyStatus, "text_only_channel_ok")
        media_summary = (
            "Text-only channel publication mode for this preview; no showcase photo required on the card."
        )
    else:
        media_status = cast(PublishingConsoleMediaPolicyStatus, "publish_safe_metadata_only")
        if sp.showcase_photo_url:
            media_summary = (
                "Showcase preview resolves a photo URL or Telegram reference; durable bytes policy is still "
                "metadata-first (B7)."
            )
        else:
            media_summary = (
                "Photo-with-caption mode in preview but no showcase photo URL; verify cover and approve-for-card gates."
            )

    eff = (st.effective_template_id or "").strip()
    if eff and st.preview_fact_lines_ro_html:
        tpl_status = cast(PublishingConsoleTemplateSourceStatus, "available")
    elif eff:
        tpl_status = cast(PublishingConsoleTemplateSourceStatus, "partial")
    else:
        tpl_status = cast(PublishingConsoleTemplateSourceStatus, "unavailable")

    tpl_summary_parts: list[str] = []
    if eff:
        tpl_summary_parts.append(f"Effective B12B template `{eff}` from packaging draft.")
    else:
        tpl_summary_parts.append("No effective marketing template id; complete packaging or template selection.")
    if st.notes:
        tpl_summary_parts.append(st.notes[0][:200])

    t_actions, c_actions = _b15f_future_template_channel_hints()
    clean_title = (title or "").strip() or f"Offer #{offer_id}"

    return {
        "source_kind": "supplier_offer",
        "source_id": offer_id,
        "source_title": clean_title,
        "template_kind": cast(PublishingConsoleTemplateKind, "supplier_offer_showcase"),
        "template_version": f"{eff}_b12b_deterministic" if eff else "packaging_pending",
        "template_source_status": tpl_status,
        "template_source_summary": " ".join(tpl_summary_parts).strip(),
        "template_preview_available": True,
        "template_preview_path": f"/admin/supplier-offers/{offer_id}/showcase-preview",
        "channel_kind": cast(PublishingConsoleChannelKind, "telegram_showcase_channel"),
        "channel_status": cast(
            PublishingConsoleChannelStatus,
            "configured" if channel_configured else "not_configured",
        ),
        "channel_ref": channel_id or None,
        "channel_summary": (
            "Telegram showcase channel id present in settings."
            if channel_configured
            else "Telegram showcase channel id missing in settings; channel publish cannot succeed until configured."
        ),
        "media_policy_status": media_status,
        "media_summary": media_summary,
        "template_actions": t_actions,
        "channel_actions": c_actions,
    }


def _b15f_tour_promotion(*, tour_id: int, title: str) -> dict[str, Any]:
    t_actions, c_actions = _b15f_future_template_channel_hints()
    return {
        "source_kind": "tour",
        "source_id": tour_id,
        "source_title": (title or "").strip() or f"Tour #{tour_id}",
        "template_kind": cast(PublishingConsoleTemplateKind, "tour_promotion_placeholder"),
        "template_version": "not_implemented",
        "template_source_status": cast(PublishingConsoleTemplateSourceStatus, "not_applicable"),
        "template_source_summary": "Tour promotion templates are not implemented in B15F (read-model placeholder only).",
        "template_preview_available": False,
        "template_preview_path": None,
        "channel_kind": cast(PublishingConsoleChannelKind, "none"),
        "channel_status": cast(PublishingConsoleChannelStatus, "not_applicable"),
        "channel_ref": None,
        "channel_summary": (
            "No supplier-offer Telegram showcase channel binding on tour promotion rows in B15F."
        ),
        "media_policy_status": cast(PublishingConsoleMediaPolicyStatus, "not_applicable"),
        "media_summary": (
            "Supplier-offer showcase cover/media gating does not apply to tour promotion placeholders."
        ),
        "template_actions": t_actions,
        "channel_actions": c_actions,
    }


_CONSOLE_PREVIEW_READ_ONLY_SAFETY = (
    "Publishing console is read-only: no Telegram publish, schedule, channel send, or worker/scheduling. "
    "Operators use separate GET/POST endpoints for preview and publish."
)

_CONSOLE_PREVIEW_TOUR_PLACEHOLDER = (
    " Tour promotion rows use placeholder templates; compose-to-channel is not implemented in this slice."
)


def _console_preview_supplier_offer(
    *,
    rp: AdminSupplierOfferReviewPackageRead,
    item_title: str,
    b15f: dict[str, Any],
    b15d: dict[str, Any],
) -> AdminPublishingConsolePreviewRead:
    pr = rp.publish_readiness
    sp = rp.showcase_preview
    st = rp.showcase_template_preview
    eff = (st.effective_template_id or "").strip() or None

    tpl_stat = b15f["template_source_status"]
    media_stat = b15f["media_policy_status"]
    tpl_preview_avail = b15f["template_preview_available"]

    if media_stat == "media_blocked":
        pstat: PublishingConsolePreviewStatus = "blocked"
    elif tpl_stat == "unavailable":
        pstat = "blocked"
    elif tpl_stat == "partial" or not tpl_preview_avail:
        pstat = "placeholder"
    else:
        pstat = "available"

    if rp.offer.payment_mode is SupplierOfferPaymentMode.ASSISTED_CLOSURE:
        tf: PublishingConsoleTemplateFamily = "custom_request_cta"
    else:
        tf = "supplier_offer_showcase"

    sales_mode_v = getattr(rp.offer.sales_mode, "value", str(rp.offer.sales_mode))
    ctk = str(b15d.get("conversion_target_kind", "none"))
    target_kind = f"{ctk}:{sales_mode_v}"

    primary_cta: str | None = None
    if (sp.cta_rezerva_href or "").strip():
        primary_cta = "Rezervă (channel preview)"
    elif (sp.cta_detalii_href or "").strip():
        primary_cta = "Detalii (channel preview)"

    summary = (b15f.get("template_source_summary") or "").strip() or None

    return AdminPublishingConsolePreviewRead(
        preview_status=pstat,
        template_family=tf,
        template_id=eff,
        template_version=(b15f.get("template_version") or None),
        title=(item_title or "").strip() or None,
        summary=summary,
        primary_cta_label=primary_cta,
        target_kind=target_kind,
        target_url=b15d.get("conversion_target_url"),
        media_status=str(media_stat),
        channel_status=str(b15f["channel_status"]),
        preview_path=b15f.get("template_preview_path"),
        safety_note=_CONSOLE_PREVIEW_READ_ONLY_SAFETY,
        next_action_code=pr.next_action_code,
        next_action_label=pr.next_action_label,
    )


def _console_preview_tour_promotion(
    *,
    tour_title: str,
    sales_mode: str,
    b15f: dict[str, Any],
    b15d: dict[str, Any],
    human_summary: str,
    console_status: PublishingConsoleItemStatus,
) -> AdminPublishingConsolePreviewRead:
    kind = b15f.get("template_kind", "none")
    if kind == "tour_promotion_placeholder":
        pstat: PublishingConsolePreviewStatus = "placeholder"
    else:
        pstat = "not_applicable"

    if console_status == "blocked":
        next_code: str | None = "resolve_tour_blockers"
        next_label: str | None = "Resolve tour listing, seats, or departure/catalog window before promotion UX."
    elif console_status == "needs_attention":
        next_code = "resolve_catalog_window"
        next_label = "Bring tour into customer-visible catalog window for promotion candidates."
    else:
        next_code = "compose_tour_promotion_not_implemented"
        next_label = "Compose tour promotion draft (not implemented; placeholder template only)."

    summary = (human_summary or "").strip() or None

    return AdminPublishingConsolePreviewRead(
        preview_status=pstat,
        template_family="tour_promotion",
        template_id=None,
        template_version=b15f.get("template_version"),
        title=(tour_title or "").strip() or None,
        summary=summary,
        primary_cta_label="Exact-tour Mini App link (when listed)" if console_status == "ready" else None,
        target_kind=f"exact_tour:{sales_mode}",
        target_url=b15d.get("conversion_target_url"),
        media_status=str(b15f["media_policy_status"]),
        channel_status=str(b15f["channel_status"]),
        preview_path=None,
        safety_note=_CONSOLE_PREVIEW_READ_ONLY_SAFETY + _CONSOLE_PREVIEW_TOUR_PLACEHOLDER,
        next_action_code=next_code,
        next_action_label=next_label,
    )


_TEMPLATE_ID_SUPPLIER_SHOWCASE = "supplier_offer_showcase"
_TEMPLATE_ID_CUSTOM_REQUEST_CTA = "custom_request_cta"
_TEMPLATE_ID_TOUR_PROMO_PLACEHOLDER = "tour_promotion_placeholder"
_TEMPLATE_ID_TOUR_PROMO_RICH_CARD = "tour_promotion_rich_card"


def _library_family_from_preview(tf: PublishingConsoleTemplateFamily) -> PublishingConsoleTemplateLibraryFamily:
    if tf == "tour_promotion":
        return "tour_promotion"
    if tf == "unknown":
        return "unknown"
    return "supplier_offer_showcase"


def _showcase_variant_status(
    *,
    tpl_stat: str,
    media_stat: str,
    tpl_preview_avail: bool,
) -> tuple[PublishingConsoleTemplateLibraryEntryStatus, str | None]:
    if media_stat == "media_blocked":
        return "blocked", "Showcase card blocked by cover/media quality policy for this offer."
    if tpl_stat == "unavailable":
        return "blocked", "No effective B12B marketing template id; complete packaging or template selection."
    if tpl_stat == "partial" or not tpl_preview_avail:
        return "blocked", "Template facts or preview path incomplete (partial template source or preview not usable)."
    return "available", None


def _template_library_supplier_offer(
    *,
    rp: AdminSupplierOfferReviewPackageRead,
    b15f: dict[str, Any],
    cp: AdminPublishingConsolePreviewRead,
) -> AdminPublishingConsoleTemplateLibraryRead:
    tpl_stat = str(b15f["template_source_status"])
    media_stat = str(b15f["media_policy_status"])
    tpl_preview_avail = bool(b15f["template_preview_available"])
    eff = (cp.template_id or "").strip() or None
    ver = (b15f.get("template_version") or "").strip() or None

    fam = _library_family_from_preview(cp.template_family)

    if rp.offer.payment_mode is SupplierOfferPaymentMode.ASSISTED_CLOSURE:
        st_show, dr_show = _showcase_variant_status(
            tpl_stat=tpl_stat,
            media_stat=media_stat,
            tpl_preview_avail=tpl_preview_avail,
        )
        cr_status: PublishingConsoleTemplateLibraryEntryStatus
        cr_reason: str | None
        if st_show == "available":
            cr_status, cr_reason = "available", None
        else:
            cr_status, cr_reason = st_show, dr_show
        entries = [
            AdminPublishingConsoleTemplateLibraryEntryRead(
                template_id=_TEMPLATE_ID_CUSTOM_REQUEST_CTA,
                label="Custom request / assisted closure CTA",
                description=(
                    "Channel card emphasizes custom-request handoff and assisted closure (not platform checkout)."
                ),
                status=cr_status,
                disabled_reason=cr_reason,
            ),
            AdminPublishingConsoleTemplateLibraryEntryRead(
                template_id=_TEMPLATE_ID_SUPPLIER_SHOWCASE,
                label="Standard supplier-offer showcase",
                description="Default B12B deterministic showcase track used for platform checkout offers.",
                status="not_applicable",
                disabled_reason="Offer is assisted-closure; standard checkout showcase is not the primary template.",
            ),
        ]
        sel = _TEMPLATE_ID_CUSTOM_REQUEST_CTA
        reason = (
            "Assisted-closure offers select the custom-request CTA variant; resolve template/media gates before publish."
        )
        return AdminPublishingConsoleTemplateLibraryRead(
            family=fam,
            selected_template_id=sel,
            recommended_template_id=sel,
            template_version=ver,
            available_templates=entries,
            selection_reason=reason,
            safety_note=_CONSOLE_PREVIEW_READ_ONLY_SAFETY,
        )

    st_sc, dr_sc = _showcase_variant_status(
        tpl_stat=tpl_stat,
        media_stat=media_stat,
        tpl_preview_avail=tpl_preview_avail,
    )
    entries = [
        AdminPublishingConsoleTemplateLibraryEntryRead(
            template_id=_TEMPLATE_ID_SUPPLIER_SHOWCASE,
            label="Supplier-offer showcase (B12B)",
            description=(
                "Deterministic showcase rendering from packaging + effective template id "
                + (f"(`{eff}`)." if eff else "(packaging pending).")
            ),
            status=st_sc,
            disabled_reason=dr_sc,
        ),
        AdminPublishingConsoleTemplateLibraryEntryRead(
            template_id=_TEMPLATE_ID_CUSTOM_REQUEST_CTA,
            label="Custom request / assisted closure CTA",
            description="Alternate emphasis for assisted-closure offers only.",
            status="not_applicable",
            disabled_reason="Platform checkout offer; custom-request CTA template is not applicable.",
        ),
    ]
    sel = eff or _TEMPLATE_ID_SUPPLIER_SHOWCASE
    reason = (
        f"Platform checkout uses the B12B showcase track; effective template id is `{eff}`."
        if eff
        else "Platform checkout uses the B12B showcase track; set effective marketing template in packaging."
    )
    return AdminPublishingConsoleTemplateLibraryRead(
        family=fam,
        selected_template_id=sel,
        recommended_template_id=eff or _TEMPLATE_ID_SUPPLIER_SHOWCASE,
        template_version=ver,
        available_templates=entries,
        selection_reason=reason,
        safety_note=_CONSOLE_PREVIEW_READ_ONLY_SAFETY,
    )


def _template_library_tour_promotion(
    *,
    b15f: dict[str, Any],
    console_status: PublishingConsoleItemStatus,
    human_summary: str,
) -> AdminPublishingConsoleTemplateLibraryRead:
    ver_raw = b15f.get("template_version")
    ver = str(ver_raw).strip() if ver_raw is not None else None
    desc_common = (human_summary or "").strip() or "Tour promotion candidate (read-only console)."
    placeholder_reason: str | None = None
    if console_status == "blocked":
        placeholder_reason = "Tour has blockers (seats, departure, or catalog window) before promotion messaging."
    elif console_status == "needs_attention":
        placeholder_reason = "Tour is not in a customer-visible catalog window for promotion candidates."
    entries = [
        AdminPublishingConsoleTemplateLibraryEntryRead(
            template_id=_TEMPLATE_ID_TOUR_PROMO_PLACEHOLDER,
            label="Tour promotion placeholder",
            description=desc_common,
            status="future",
            disabled_reason=placeholder_reason
            or "Compose-to-channel promotion templates are not implemented; console is read-only.",
        ),
        AdminPublishingConsoleTemplateLibraryEntryRead(
            template_id=_TEMPLATE_ID_TOUR_PROMO_RICH_CARD,
            label="Rich tour promotion card",
            description="Future variant for stylized last-seats / promotion posts tied to catalog tours.",
            status="future",
            disabled_reason="Not implemented; forward B15+ design.",
        ),
    ]
    sel = _TEMPLATE_ID_TOUR_PROMO_PLACEHOLDER
    reason = (
        "Tour promotion rows only expose placeholder template keys; "
        "no channel compose or publish from this endpoint."
    )
    return AdminPublishingConsoleTemplateLibraryRead(
        family="tour_promotion",
        selected_template_id=sel,
        recommended_template_id=sel,
        template_version=ver,
        available_templates=entries,
        selection_reason=reason,
        safety_note=_CONSOLE_PREVIEW_READ_ONLY_SAFETY + _CONSOLE_PREVIEW_TOUR_PLACEHOLDER,
    )


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
            b15d = _b15d_supplier_offer(
                session,
                offer_id=row.id,
                rp=rp,
                console_status=status,
                blocked_reasons=br,
            )
            actions = _affordances_from_operator_workflow(rp, row.id)
            item_title = (row.title or f"Offer #{row.id}").strip() or f"Offer #{row.id}"
            b15f = _b15f_supplier_offer(
                settings=get_settings(),
                rp=rp,
                offer_id=row.id,
                title=item_title,
            )
            cp = _console_preview_supplier_offer(
                rp=rp,
                item_title=item_title,
                b15f=b15f,
                b15d=b15d,
            )
            tl = _template_library_supplier_offer(rp=rp, b15f=b15f, cp=cp)
            item = AdminPublishingConsoleItemRead(
                candidate_key=f"supplier_offer:{row.id}",
                kind="supplier_offer_initial",
                console_status=status,
                title=item_title,
                subtitle=f"Lifecycle {row.lifecycle_status}",
                target_summary=_target_summary_offer(rp),
                next_best_action=rp.operator_workflow.primary_next_action or (
                    rp.recommended_next_actions[0] if rp.recommended_next_actions else None
                ),
                blocked_reasons=br,
                human_summary=_human_summary_offer(rp, status),
                review_package_path=f"/admin/supplier-offers/{row.id}/review-package",
                prepare_conversion_chain_plan_path=supplier_offer_prepare_conversion_chain_plan_path(row.id),
                prepare_conversion_chain_plan_status=rp.prepare_conversion_chain_plan_status,
                prepare_conversion_chain_recommended_action=rp.prepare_conversion_chain_recommended_action,
                prepare_conversion_chain_blockers_count=rp.prepare_conversion_chain_blockers_count,
                prepare_conversion_chain_action=rp.prepare_conversion_chain_action,
                publish_readiness=rp.publish_readiness,
                console_preview=cp,
                template_library=tl,
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
                actions=actions,
                **b15d,
                **b15f,
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
            b15d = _b15d_tour_promotion(
                tour_id=t.id,
                tour_code=t.code,
                console_status=status,
                blocked_reasons=br,
                human_summary=human,
                tour_status=t.status.value,
                sales_mode=t.sales_mode.value,
                seats_available=t.seats_available,
            )
            t_actions = _tour_promotion_action_affordances(tour_id=t.id)
            tour_title = (t.title_default or t.code or f"Tour #{t.id}").strip()
            b15f = _b15f_tour_promotion(tour_id=t.id, title=tour_title)
            pr_row = publish_readiness_for_tour_promotion(generated_at=now)
            cp = _console_preview_tour_promotion(
                tour_title=tour_title,
                sales_mode=t.sales_mode.value,
                b15f=b15f,
                b15d=b15d,
                human_summary=human,
                console_status=status,
            )
            tl = _template_library_tour_promotion(
                b15f=b15f,
                console_status=status,
                human_summary=human,
            )
            enriched.append(
                (
                    t.departure_datetime,
                    AdminPublishingConsoleItemRead(
                        candidate_key=f"tour:{t.id}",
                        kind="tour_promotion",
                        console_status=status,
                        title=tour_title,
                        subtitle=f"{t.code} · {t.sales_mode.value}",
                        target_summary=f"exact_tour · /mini-app/tours/{t.code} (conceptual; B15D template)",
                        next_best_action="compose_tour_promotion_draft" if status == "ready" else "resolve_tour_blockers",
                        blocked_reasons=br,
                        human_summary=human,
                        review_package_path=None,
                        publish_readiness=pr_row,
                        console_preview=cp,
                        template_library=tl,
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
                        actions=t_actions,
                        **b15d,
                        **b15f,
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
