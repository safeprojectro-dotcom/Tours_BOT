"""A2: supplier offer intake validation — read-only heuristics over publishing console rows."""

from __future__ import annotations

from app.schemas.admin_publishing_console import AdminPublishingConsoleItemRead
from app.schemas.supplier_offer_intake_validation import SupplierOfferIntakeValidationRead


class SupplierOfferIntakeValidationService:
    """Builds ``SupplierOfferIntakeValidationRead`` from ``AdminPublishingConsoleItemRead`` (no DB / no mutations)."""

    _MIN_BODY_LEN_REQUIRED = 40
    _MIN_BODY_LEN_COMFORTABLE = 160
    _MIN_TITLE_LEN_COMFORTABLE = 8

    @classmethod
    def build_from_console_item(
        cls,
        item: AdminPublishingConsoleItemRead,
    ) -> SupplierOfferIntakeValidationRead | None:
        if item.kind != "supplier_offer_initial":
            return None

        od = item.offer_debug
        supplier_offer_id = int(od.supplier_offer_id) if od is not None else int(item.source_id)

        payload = item.preview_payload
        pr = item.publish_readiness
        title = (item.title or "").strip()
        body = (payload.body_text or "").strip()
        cta = (payload.primary_cta_url or "").strip()
        media_ref = (payload.media_reference or "").strip()

        present: list[str] = []
        missing: list[str] = []
        weak: list[str] = []
        pub_blocks: list[str] = []
        conv_blocks: list[str] = []
        ask_next: list[str] = []

        def _push_unique(bucket: list[str], value: str) -> None:
            v = value.strip()
            if v and v not in bucket:
                bucket.append(v)

        if len(title) >= 3:
            _push_unique(present, "offer_list_title")
        else:
            _push_unique(missing, "offer_list_title")

        if item.subtitle and str(item.subtitle).strip():
            _push_unique(present, "row_subtitle")

        if len(title) >= cls._MIN_TITLE_LEN_COMFORTABLE:
            _push_unique(present, "offer_title_descriptive")
        elif title:
            _push_unique(weak, "offer_title_descriptive")

        pt = (payload.title or "").strip()
        if pt:
            _push_unique(present, "preview_customer_title")

        if len(body) >= cls._MIN_BODY_LEN_REQUIRED:
            _push_unique(present, "preview_customer_body")
            if len(body) < cls._MIN_BODY_LEN_COMFORTABLE:
                _push_unique(weak, "preview_customer_body_depth")
        else:
            _push_unique(missing, "preview_customer_body")

        if cta:
            _push_unique(present, "preview_primary_cta")
        else:
            _push_unique(missing, "preview_primary_cta")

        if media_ref:
            _push_unique(present, "preview_media_reference")
        elif item.media_policy_status in ("media_blocked", "media_review_pending"):
            _push_unique(weak, "preview_media_reference")

        if od is not None:
            _push_unique(present, "offer_debug.lifecycle_packaging_snapshot")
            lifecycle = (od.lifecycle_status or "").strip().lower()
            packaging = (od.packaging_status or "").strip().lower()
            if lifecycle in ("draft", "rejected"):
                _push_unique(weak, f"lifecycle:{lifecycle or 'unknown'}")
            if packaging and packaging != "approved_for_publish":
                _push_unique(weak, f"packaging:{packaging}")
            if not od.can_publish_now:
                _push_unique(pub_blocks, "offer_debug.flags_publish_not_ready")

        if item.channel_status == "configured":
            _push_unique(present, "channel_configured_hint")

        if pr.status == "blocked":
            _push_unique(pub_blocks, "publish_readiness:blocked")
        elif pr.status == "needs_review":
            _push_unique(weak, "publish_readiness:needs_review")
        elif pr.status == "ready_to_suggest":
            _push_unique(present, "publish_readiness:ready_to_suggest")

        fb = (pr.primary_blocker or "").strip()
        if fb:
            _push_unique(pub_blocks, f"publish_readiness:{fb}")
            _push_unique(ask_next, fb)

        for gate in pr.gates:
            if gate.status == "failed":
                reason = (gate.reason or gate.label or gate.code or "").strip()
                if reason:
                    _push_unique(pub_blocks, f"gate:{gate.code}:{reason}")
                    _push_unique(ask_next, reason)
                else:
                    _push_unique(pub_blocks, f"gate_failed:{gate.code}")
            elif gate.status == "warning":
                r = (gate.reason or gate.label or gate.code or "").strip()
                if r:
                    _push_unique(weak, f"gate_warning:{gate.code}:{r}")

        for b in item.blocked_reasons or []:
            s = str(b).strip()
            if s:
                _push_unique(pub_blocks, f"console_blocked_reason:{s}")

        pb = (item.primary_blocker or "").strip()
        if pb:
            _push_unique(pub_blocks, f"console_primary_blocker:{pb}")

        for x in payload.blockers or []:
            s = str(x).strip()
            if s:
                _push_unique(pub_blocks, f"preview_payload_blocker:{s}")
                _push_unique(ask_next, s)

        for w in payload.warnings or []:
            s = str(w).strip()
            if s:
                _push_unique(weak, f"preview_warning:{s}")
                _push_unique(ask_next, s)

        if item.media_policy_status == "media_blocked":
            _push_unique(pub_blocks, "media_policy:media_blocked")

        st = item.prepare_conversion_chain_plan_status
        if st in ("blocked", "ineligible"):
            lbl = (item.prepare_conversion_chain_recommended_action or st or "").strip()
            _push_unique(conv_blocks, f"prepare_chain:{st}:{lbl}" if lbl else f"prepare_chain:{st}")
        elif st == "partial":
            _push_unique(conv_blocks, "prepare_chain:partial")

        cta_safe = item.cta_safety_status
        if cta_safe in ("missing_execution_link", "tour_not_listed", "media_blocked"):
            _push_unique(conv_blocks, f"cta_safety:{cta_safe}")

        if item.conversion_target_kind == "none" and item.kind == "supplier_offer_initial":
            _push_unique(conv_blocks, "conversion_target:none")

        nxt = (od.next_missing_step if od is not None else None) or ""
        if nxt.strip():
            _push_unique(ask_next, nxt.strip())

        for code in ("preview_customer_body", "preview_primary_cta"):
            if code in missing:
                if code == "preview_customer_body":
                    _push_unique(
                        ask_next,
                        "Supplier: provide a fuller program/description suitable for the customer-facing preview body.",
                    )
                else:
                    _push_unique(
                        ask_next,
                        "Supplier: confirm the primary booking/details link (Mini App or governed URL) for the CTA.",
                    )

        # Headline synthesis (short, admin-triage oriented)
        headline_parts: list[str] = []
        if missing:
            headline_parts.append(f"missing:{len(missing)}")
        if pub_blocks:
            headline_parts.append("publication blocked")
        elif weak and not missing:
            headline_parts.append("needs polish")
        if conv_blocks:
            headline_parts.append("conversion not green")
        if not headline_parts:
            headline_parts.append("intake looks sufficient at console-row granularity")
        headline = "; ".join(headline_parts)

        return SupplierOfferIntakeValidationRead(
            supplier_offer_id=supplier_offer_id,
            headline=headline,
            facts_present=present,
            facts_missing_required=missing,
            facts_weak_or_unclear=weak,
            blocks_publication=pub_blocks,
            blocks_catalog_conversion=conv_blocks,
            suggested_supplier_requests=ask_next[:12],
        )


__all__ = ["SupplierOfferIntakeValidationService"]
