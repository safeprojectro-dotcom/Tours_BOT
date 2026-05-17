"""A1V–A1V4: Automation Cockpit Telegram formatters and callback tests (read-only)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.bot.constants import ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX
from app.bot.automation_cockpit_telegram import (
    cockpit_card_callback,
    cockpit_card_keyboard,
    cockpit_queue_keyboard,
    cockpit_summary_keyboard,
    find_card_in_cockpit,
    format_admin_datetime_compact,
    format_cockpit_card_detail_text,
    format_cockpit_queue_text,
    format_cockpit_safety_detail_text,
    format_cockpit_summary_text,
    parse_cockpit_card_callback,
)
from app.schemas.admin_automation_cockpit import (
    AdminAutomationCockpitCardRead,
    AdminAutomationCockpitCardSafetyFlagsRead,
    AdminAutomationCockpitCommercialContextRead,
    AdminAutomationCockpitQueryRead,
    AdminAutomationCockpitQueueRead,
    AdminAutomationCockpitRead,
    AdminAutomationCockpitSafetySummaryRead,
    AdminAutomationCockpitSummaryRead,
)
from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead
from app.schemas.supplier_offer_intake_validation import SupplierOfferIntakeValidationRead
from app.schemas.supplier_offer_catalog_conversion_readiness import (
    CatalogConversionGuidedActionRead,
    SupplierOfferCatalogConversionReadinessRead,
)
from app.services.supplier_clarification_draft_service import SupplierClarificationDraftService


def _sample_safety_summary() -> AdminAutomationCockpitSafetySummaryRead:
    return AdminAutomationCockpitSafetySummaryRead(
        note="read-only test",
    )


def _sample_card(
    *,
    commercial: bool = False,
    source_type: str = "supplier_offer",
    source_id: int = 42,
    source_paths: dict[str, str] | None = None,
    blocker_summary: str | None = None,
    catalog_conversion_readiness: SupplierOfferCatalogConversionReadinessRead | None = None,
) -> AdminAutomationCockpitCardRead:
    ctx = (
        AdminAutomationCockpitCommercialContextRead(
            tour_code="TC1",
            fact_lock_note="FACT_LOCK_NOTE_TEST",
        )
        if commercial
        else None
    )
    resolved_blocker = (
        "Package must be approved for publishing." if blocker_summary is None else blocker_summary
    )
    return AdminAutomationCockpitCardRead(
        card_id="x",
        source_type=source_type,
        source_id=source_id,
        title="Test Offer",
        status="needs_attention",
        status_label="Needs attention",
        status_tone="warning",
        priority=1,
        next_best_action_code="review_missing_marketing_data",
        next_best_action_label="Review missing marketing data",
        next_best_action_kind="safe_read",
        next_best_action_enabled=True,
        blocker_summary=resolved_blocker,
        commercial_context=ctx,
        safety_flags=AdminAutomationCockpitCardSafetyFlagsRead(),
        source_paths=source_paths or {},
        catalog_conversion_readiness=catalog_conversion_readiness,
        metadata={"console_status": "needs_attention"},
    )


def _sample_read(*, commercial: bool = False) -> AdminAutomationCockpitRead:
    summary = AdminAutomationCockpitSummaryRead(
        total_cards=3,
        queue_counts={
            "supplier_intake": 1,
            "missing_info": 2,
            "offer_readiness": 0,
            "risk_conflict": 0,
            "marketing_review": 3,
            "publishing_queue": 3,
            "catalog_conversion": 3,
        },
        urgent_count=1,
        needs_attention_count=0,
        ready_count=2,
        blocked_count=0,
        future_disabled_count=0,
    )
    card = _sample_card(commercial=commercial)
    q = AdminAutomationCockpitQueueRead(
        queue_code="marketing_review",
        queue_label="Marketing",
        queue_status="active",
        queue_tone="neutral",
        total_count=1,
        cards=[card],
        description="d",
        next_refresh_hint="h",
    )
    return AdminAutomationCockpitRead(
        generated_at=datetime.now(UTC),
        summary=summary,
        queues=[q],
        safety_summary=_sample_safety_summary(),
        source_note="unit",
        query=AdminAutomationCockpitQueryRead(
            limit_per_queue=5,
            include_queues=None,
            publishing_console_limit=120,
            publishing_console_kind=None,
        ),
    )


def test_format_admin_datetime_compact_iso() -> None:
    assert format_admin_datetime_compact("en", "2026-04-28T18:00:00+00:00") == "28.04.2026, 18:00"
    assert format_admin_datetime_compact("ro", "2026-04-28 18:00+00:00") == "28.04.2026, 18:00"


def test_format_cockpit_summary_demo_ready_no_raw_codes() -> None:
    body = format_cockpit_summary_text("en", _sample_read())
    assert "📊 Admin automation cockpit" in body
    assert "Total: 3 cards" in body
    assert "🚨 Urgent: 1" in body
    assert "🛡 Safe mode" in body
    assert "supplier_intake" not in body
    assert "read_only=" not in body
    assert "📥 Supplier intake: 1" in body
    assert "🔒 Supplier/catalog facts stay locked" in body


def test_format_cockpit_safety_detail_includes_flags() -> None:
    body = format_cockpit_safety_detail_text("en", _sample_read())
    assert "Safety flags" in body
    assert "read_only=" in body


def test_format_cockpit_queue_lists_cards_without_technical_junk() -> None:
    r = _sample_read()
    body = format_cockpit_queue_text("en", r, queue_code="marketing_review")
    assert "🧩 Marketing review" in body
    assert "Test Offer" in body
    assert "Offer #42" in body
    assert "1) Test Offer" in body
    assert "Needs attention" in body or "⚠️" in body
    assert "Reason:" in body
    assert "Step:" in body
    assert "Check missing marketing data" in body
    assert "Package must" in body
    assert "safe_read" not in body
    assert "kind=" not in body
    assert "Status:" not in body


def test_format_cockpit_queue_list_ro_standard_lines() -> None:
    r = _sample_read()
    body = format_cockpit_queue_text("ro", r, queue_code="marketing_review")
    assert "Motiv:" in body
    assert "Pas:" in body
    assert "Necesită atenție" in body
    assert "Verifică datele marketing lipsă" in body
    assert "Review missing" not in body


def test_format_cockpit_queue_humanizes_blocker_and_strips_debug_paren() -> None:
    r = _sample_read()
    r.queues[0].cards[0].blocker_summary = "Departure is in the past."
    body = format_cockpit_queue_text("en", r, queue_code="marketing_review")
    assert "Departure date is in the past" in body
    r2 = _sample_read()
    r2.queues[0].cards[0].blocker_summary = ""
    r2.queues[0].cards[0].warning_summary = (
        "Candidate for tour promotion / last-seats style posts (B15B does not send)."
    )
    body2 = format_cockpit_queue_text("en", r2, queue_code="marketing_review")
    assert "B15B" not in body2
    assert "does not send" not in body2.lower()


def test_format_cockpit_card_detail_catalog_gates_humanized_en() -> None:
    c = _sample_card()
    c.blocker_summary = "Not ideal for catalog promotion until gates pass."
    body = format_cockpit_card_detail_text("en", c)
    assert "Not ready for catalog promotion" in body
    assert "gates pass" not in body.lower()


def test_format_cockpit_card_detail_a6a_ro_humanized_no_message_keys() -> None:
    snap = SupplierOfferCatalogConversionReadinessRead(
        readiness_status="needs_internal_preparation",
        status_label_message_key="admin_a6a_status_needs_preparation",
        main_blocker_message_key="admin_a6a_blocker_offer_tour_link",
        warnings_message_keys=["admin_a6a_warn_prepare_partial"],
        next_step_message_key="admin_a6a_next_prepare_offer_tour_link",
        has_tour_link=False,
        has_execution_link=False,
        mini_app_cta_safe=False,
        catalog_visible=False,
    )
    c = _sample_card(blocker_summary="", catalog_conversion_readiness=snap, commercial=True)
    body = format_cockpit_card_detail_text("ro", c)
    assert "🧭 Catalog / conversie" in body
    assert "Necesită pregătire" in body
    assert "admin_a6a_" not in body
    assert "cta_safety" not in body.lower()
    assert "prepare_chain:" not in body


def test_cockpit_card_keyboard_a6b_links_operator_workflow_not_mutation_shortcuts() -> None:
    snap = SupplierOfferCatalogConversionReadinessRead(
        readiness_status="needs_internal_preparation",
        status_label_message_key="admin_a6a_status_needs_preparation",
        main_blocker_message_key="admin_a6a_blocker_offer_tour_link",
        warnings_message_keys=[],
        next_step_message_key="admin_a6a_next_prepare_offer_tour_link",
        has_tour_link=False,
        has_execution_link=False,
        mini_app_cta_safe=False,
        catalog_visible=False,
        guided_actions=[
            CatalogConversionGuidedActionRead(
                label_message_key="admin_a6b_btn_continue_in_operator_workflow",
                callback_data=f"{ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX}42",
            ),
        ],
    )
    c = _sample_card(catalog_conversion_readiness=snap)
    kb = cockpit_card_keyboard(
        "en",
        queue_code="catalog_conversion",
        card_refresh_callback=cockpit_card_callback("catalog_conversion", "supplier_offer", 42),
        card=c,
    )
    flat = [b for row in kb.as_markup().inline_keyboard for b in row]
    callbacks = [x.callback_data for x in flat if getattr(x, "callback_data", None)]
    assert any(x and str(x).startswith(ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX) for x in callbacks)
    joined = " ".join(str(x) for x in callbacks if x)
    assert "ao:ow:tbp:" not in joined
    labels = [x.text for x in flat]
    assert not any("admin_a6b" in t for t in labels)


def test_cockpit_card_keyboard_a6b_ready_includes_mini_app_url_when_set() -> None:
    snap = SupplierOfferCatalogConversionReadinessRead(
        readiness_status="ready_for_review",
        status_label_message_key="admin_a6a_status_ready_for_review",
        main_blocker_message_key=None,
        warnings_message_keys=[],
        next_step_message_key="admin_a6a_next_verify_mini_app",
        has_tour_link=True,
        has_execution_link=True,
        mini_app_cta_safe=True,
        catalog_visible=True,
        guided_actions=[
            CatalogConversionGuidedActionRead(
                label_message_key="admin_a6b_btn_verify_in_operator_workflow",
                callback_data=f"{ADMIN_OPS_OW_REVIEW_REFRESH_PREFIX}99",
            ),
            CatalogConversionGuidedActionRead(
                label_message_key="admin_a6b_btn_open_mini_app",
                url="https://mini.example/open",
            ),
        ],
    )
    c = _sample_card(catalog_conversion_readiness=snap, source_type="supplier_offer", source_id=99)
    kb = cockpit_card_keyboard(
        "en",
        queue_code="offer_readiness",
        card_refresh_callback=cockpit_card_callback("offer_readiness", "supplier_offer", 99),
        card=c,
    )
    flat = [b for row in kb.as_markup().inline_keyboard for b in row]
    urls = [x.url for x in flat if x.url]
    assert "https://mini.example/open" in urls


def test_format_cockpit_queue_includes_a6a_hint_when_present() -> None:
    snap = SupplierOfferCatalogConversionReadinessRead(
        readiness_status="ready_for_review",
        status_label_message_key="admin_a6a_status_ready_for_review",
        main_blocker_message_key=None,
        warnings_message_keys=[],
        next_step_message_key="admin_a6a_next_verify_mini_app",
        has_tour_link=True,
        has_execution_link=True,
        mini_app_cta_safe=True,
        catalog_visible=True,
    )
    r = _sample_read()
    r.queues[0].cards[0].catalog_conversion_readiness = snap
    body = format_cockpit_queue_text("en", r, queue_code="marketing_review")
    assert "Step:" in body
    assert "Verify the tour in the Mini App before publishing" in body
    assert body.count("🧭") == 0


def test_format_cockpit_card_detail_dedupes_internal_tasks() -> None:
    from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead

    c = _sample_card()
    c.clarification_draft = SupplierClarificationDraftRead(
        supplier_offer_id=42,
        supplier_facing_asks=[],
        supplier_facing_message_ro=None,
        internal_admin_tasks=[
            "gate:showcase_media:media_review_replacement_requested",
            "preview: media_review_replacement extra",
            "media_review_replacement_requested:foo",
        ],
    )
    body = format_cockpit_card_detail_text("en", c)
    assert body.count("• ") == 1
    assert "showcase photo" in body.lower()


def test_humanize_admin_technical_unknown_short_fallback() -> None:
    from app.bot.automation_cockpit_telegram import humanize_admin_text

    assert humanize_admin_text("en", "totally_opaque_debug_token_xyz") == "Requires internal verification."
    assert humanize_admin_text("ro", "totally_opaque_debug_token_xyz") == "Necesită verificare internă."


def test_format_cockpit_card_detail_internal_tasks_cap_five_overflow_en() -> None:
    from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead

    tasks = [
        "prepare_chain:blocked",
        "cta_safety:warn",
        "gate:showcase_media:x",
        "missing_execution:1",
        "content_quality:y",
        "description_thin:z",
    ]
    c = _sample_card()
    c.clarification_draft = SupplierClarificationDraftRead(
        supplier_offer_id=1,
        supplier_facing_asks=[],
        supplier_facing_message_ro=None,
        internal_admin_tasks=tasks,
    )
    body = format_cockpit_card_detail_text("en", c)
    assert body.count("• ") == 6
    assert "Additional internal tasks exist" in body
    assert "prepare_chain" not in body.lower()
    assert "cta_safety" not in body.lower()


def test_format_cockpit_card_detail_internal_tasks_no_overflow_at_five_ro() -> None:
    from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead

    tasks = [
        "prepare_chain:a",
        "cta_safety:b",
        "gate:c",
        "missing_execution:d",
        "content_quality:e",
    ]
    c = _sample_card()
    c.clarification_draft = SupplierClarificationDraftRead(
        supplier_offer_id=1,
        supplier_facing_asks=[],
        supplier_facing_message_ro=None,
        internal_admin_tasks=tasks,
    )
    body = format_cockpit_card_detail_text("ro", c)
    assert body.count("• ") == 5
    assert "Mai există sarcini" not in body


def test_format_cockpit_card_detail_internal_tasks_overflow_ro_message() -> None:
    from app.schemas.supplier_clarification_draft import SupplierClarificationDraftRead

    tasks = [
        "prepare_chain:a",
        "cta_safety:b",
        "gate:showcase_media:x",
        "missing_execution:d",
        "content_quality:e",
        "description_thin:z",
    ]
    c = _sample_card()
    c.clarification_draft = SupplierClarificationDraftRead(
        supplier_offer_id=1,
        supplier_facing_asks=[],
        supplier_facing_message_ro=None,
        internal_admin_tasks=tasks,
    )
    body = format_cockpit_card_detail_text("ro", c)
    assert "Mai există sarcini interne suplimentare" in body


def test_supplier_clarification_draft_unchanged_when_rendering_many_internals() -> None:
    iv = SupplierOfferIntakeValidationRead(
        supplier_offer_id=42,
        headline="missing:1; publication blocked",
        facts_missing_required=["preview_customer_body"],
        suggested_supplier_requests=["prepare_chain:blocked"],
    )
    cd = SupplierClarificationDraftService.build_from_intake_validation(iv)
    cd2 = SupplierClarificationDraftService.build_from_intake_validation(iv)
    assert cd.supplier_facing_asks == cd2.supplier_facing_asks
    assert cd.supplier_facing_message_ro == cd2.supplier_facing_message_ro
    extra = list(cd.internal_admin_tasks) + [
        "cta_safety:x",
        "gate:showcase_media:y",
        "missing_execution:z",
        "content_quality:w",
        "description_thin:q",
        "offer_debug:r",
    ]
    c = _sample_card()
    c.clarification_draft = SupplierClarificationDraftRead(
        supplier_offer_id=cd.supplier_offer_id,
        supplier_facing_asks=list(cd.supplier_facing_asks),
        supplier_facing_message_ro=cd.supplier_facing_message_ro,
        internal_admin_tasks=extra,
    )
    body = format_cockpit_card_detail_text("ro", c)
    assert "Bună ziua" in body
    assert "prepare_chain" not in body.lower()


def test_format_cockpit_queue_tour_source_caption() -> None:
    r = _sample_read()
    r.queues[0].cards = [_sample_card(source_type="tour")]
    body = format_cockpit_queue_text("en", r, queue_code="marketing_review")
    assert "Tour #42" in body


def test_format_cockpit_card_detail_clarification_drafts_block() -> None:
    iv = SupplierOfferIntakeValidationRead(
        supplier_offer_id=42,
        headline="missing:1; publication blocked",
        facts_missing_required=["preview_customer_body"],
        suggested_supplier_requests=["prepare_chain:blocked"],
    )
    cd = SupplierClarificationDraftService.build_from_intake_validation(iv)
    c = _sample_card()
    c.intake_validation = iv
    c.clarification_draft = cd
    body = format_cockpit_card_detail_text("ro", c)
    assert "📋 Validare" in body
    assert "Pentru furnizor" in body
    assert "Bună ziua" in body
    assert "descriere" in body.lower()
    assert "Sarcini interne" in body
    assert "prepare_chain" not in body.lower()


def test_format_cockpit_card_detail_commercial_and_fact_lock() -> None:
    c = _sample_card(
        commercial=True,
        source_paths={"admin_tour_path": "/admin/tours/2", "admin_action_path": ""},
    )
    body = format_cockpit_card_detail_text("en", c)
    assert "📄 Card detail" in body
    assert "In short:" in body
    assert "➡" in body or "Next:" in body
    assert "Check missing marketing data" in body
    assert "Package must" in body
    assert "Commercial data:" in body
    assert "Tour code: TC1" in body
    assert "FACT_LOCK_NOTE_TEST" not in body
    assert "Prices, route" in body or "wording" in body.lower()
    assert "🔒" in body
    assert "🛡 Safety:" in body
    assert "✅ Read-only view" in body
    assert "read_only=" not in body
    assert "admin_tour_path" not in body
    assert "No scheduler jobs" not in body
    assert "admin_action_path" not in body


def test_format_cockpit_card_detail_ro_business_readable() -> None:
    c = _sample_card(source_paths={"admin_tour_path": "https://example.com/t", "admin_action_path": "https://example.com/a"})
    body = format_cockpit_card_detail_text("ro", c)
    assert "📄 Detaliu card" in body
    assert "Pe scurt:" in body
    assert "➡" in body or "Pas:" in body
    assert "Surse:" not in body
    assert "🛡 Siguranță:" in body
    assert "✅ Doar citire" in body
    assert "read_only=" not in body
    assert "admin_tour_path" not in body
    assert "Fără planificator" not in body


def test_format_cockpit_card_detail_tour_promotion_ro() -> None:
    c = _sample_card(
        source_type="tour",
        source_paths={"admin_tour_path": "/admin/tours/2", "admin_action_path": "/admin/tours/2"},
    )
    c.source_id = 2
    c.next_best_action_code = "open_tour_admin"
    c.next_best_action_label = "Open tour in admin"
    c.blocker_summary = None
    c.warning_summary = "Candidate for tour promotion / last-seats style posts."
    c.risk_summary = None
    c.metadata = {"console_status": "ready"}
    body = format_cockpit_card_detail_text("ro", c)
    assert "Tur #2" in body
    assert "Deschide turul în admin" in body
    assert "Open tour in admin" not in body
    assert "ultimele locuri" in body
    assert "admin_tour_path" not in body


def test_cockpit_outbox_callbacks_roundtrip() -> None:
    from app.bot.automation_cockpit_telegram import (
        cockpit_outbox_list_callback,
        cockpit_outbox_save_callback,
        parse_cockpit_outbox_list_callback,
        parse_cockpit_outbox_save_callback,
    )

    save_cb = cockpit_outbox_save_callback("marketing_review", "supplier_offer", 7)
    assert parse_cockpit_outbox_save_callback(save_cb) == ("marketing_review", "supplier_offer", 7)
    list_cb = cockpit_outbox_list_callback("missing_info", "supplier_offer", 99)
    assert parse_cockpit_outbox_list_callback(list_cb) == ("missing_info", "supplier_offer", 99)


def test_cockpit_outbox_item_and_status_callbacks_roundtrip() -> None:
    from app.bot.automation_cockpit_telegram import (
        OUTBOX_STATUS_VERB_CANCEL,
        OUTBOX_STATUS_VERB_READY,
        cockpit_outbox_item_open_callback,
        cockpit_outbox_status_callback,
        parse_cockpit_outbox_item_callback,
        parse_cockpit_outbox_status_callback,
    )

    oi = cockpit_outbox_item_open_callback("marketing_review", "supplier_offer", 12, 34)
    assert parse_cockpit_outbox_item_callback(oi) == ("marketing_review", "supplier_offer", 12, 34)

    ox = cockpit_outbox_status_callback("marketing_review", "supplier_offer", 12, 34, OUTBOX_STATUS_VERB_READY)
    assert parse_cockpit_outbox_status_callback(ox) == (
        "marketing_review",
        "supplier_offer",
        12,
        34,
        OUTBOX_STATUS_VERB_READY,
    )
    ox2 = cockpit_outbox_status_callback("missing_info", "supplier_offer", 5, 6, OUTBOX_STATUS_VERB_CANCEL)
    assert parse_cockpit_outbox_status_callback(ox2) == ("missing_info", "supplier_offer", 5, 6, OUTBOX_STATUS_VERB_CANCEL)


def test_outbox_save_list_callbacks_use_draft_supplier_offer_id_when_card_source_differs() -> None:
    """Save + list must encode clarification_draft.supplier_offer_id (DB/outbox key), not card.source_id."""
    from app.bot.automation_cockpit_telegram import (
        cockpit_card_keyboard,
        cockpit_refresh_callback_for_outbox_card,
        find_cockpit_card_for_clarification_outbox,
        parse_cockpit_card_callback,
        parse_cockpit_outbox_list_callback,
        parse_cockpit_outbox_save_callback,
    )

    c = _sample_card()
    c.source_type = "supplier_offer"
    c.source_id = 999
    c.clarification_draft = SupplierClarificationDraftRead(
        supplier_offer_id=42,
        supplier_facing_asks=["x"],
    )
    r = _sample_read()
    r.queues[0].cards = [c]

    refresh = parse_cockpit_card_callback(
        cockpit_refresh_callback_for_outbox_card(r, queue_code="marketing_review", supplier_offer_id=42)
    )
    assert refresh == ("marketing_review", "supplier_offer", 999)

    assert find_cockpit_card_for_clarification_outbox(r, queue_code="marketing_review", supplier_offer_id=42) is c

    kb = cockpit_card_keyboard(
        "en",
        queue_code="marketing_review",
        card_refresh_callback="ac:c:x",
        card=c,
    )
    cbs = [btn.callback_data for row in kb.export() for btn in row if btn.callback_data]
    save_cb = next(x for x in cbs if str(x).startswith("ac:os:"))
    list_cb = next(x for x in cbs if str(x).startswith("ac:ol:"))
    assert parse_cockpit_outbox_save_callback(save_cb)[2] == 42
    assert parse_cockpit_outbox_list_callback(list_cb)[2] == 42


def test_cockpit_outbox_list_and_detail_keyboards_no_publish() -> None:
    from app.bot.automation_cockpit_telegram import (
        cockpit_card_callback,
        cockpit_outbox_item_detail_keyboard,
        cockpit_outbox_list_callback,
        cockpit_outbox_list_keyboard,
    )

    from app.schemas.supplier_clarification_outbox import SupplierClarificationOutboxItemRead

    refresh = cockpit_card_callback("marketing_review", "supplier_offer", 1)
    item = SupplierClarificationOutboxItemRead(
        id=9,
        supplier_offer_id=1,
        workflow_status="draft",
        draft_snapshot={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    list_kb = cockpit_outbox_list_keyboard(
        "en",
        queue_code="marketing_review",
        source_type="supplier_offer",
        supplier_offer_id=1,
        items=[item],
        card_refresh_callback=refresh,
    )
    detail_kb = cockpit_outbox_item_detail_keyboard(
        "en",
        queue_code="marketing_review",
        card_source_type="supplier_offer",
        supplier_offer_id=1,
        item=item,
        list_callback=cockpit_outbox_list_callback("marketing_review", "supplier_offer", 1),
        card_refresh_callback=refresh,
    )
    for kb in (list_kb, detail_kb):
        for row in kb.export():
            for btn in row:
                assert btn.callback_data is not None
                low = btn.callback_data.lower()
                assert "publish" not in low
                assert "channel" not in low


def test_cockpit_card_keyboard_outbox_buttons_when_clarification_draft() -> None:
    from app.bot.automation_cockpit_telegram import cockpit_card_callback, cockpit_card_keyboard

    iv = SupplierOfferIntakeValidationRead(
        supplier_offer_id=42,
        headline="x",
        facts_missing_required=["preview_customer_body"],
        suggested_supplier_requests=[],
    )
    cd = SupplierClarificationDraftService.build_from_intake_validation(iv)
    c = _sample_card()
    c.source_type = "supplier_offer"
    c.source_id = iv.supplier_offer_id
    c.clarification_draft = cd
    refresh = cockpit_card_callback("marketing_review", "supplier_offer", c.source_id)
    kb = cockpit_card_keyboard("en", queue_code="marketing_review", card_refresh_callback=refresh, card=c)
    cbs = {btn.callback_data for row in kb.export() for btn in row}
    assert any(str(cb).startswith("ac:os:") for cb in cbs)
    assert any(str(cb).startswith("ac:ol:") for cb in cbs)


def test_cockpit_keyboards_no_publish_callbacks() -> None:
    kb = cockpit_summary_keyboard("en")
    for row in kb.export():
        for btn in row:
            assert btn.callback_data is not None
            low = btn.callback_data.lower()
            assert "publish" not in low
            assert "channel" not in low


def test_cockpit_summary_keyboard_has_safety_detail() -> None:
    kb = cockpit_summary_keyboard("en")
    callbacks = {btn.callback_data for row in kb.export() for btn in row}
    assert "ac:s" in callbacks


def test_cockpit_queue_keyboard_only_navigation_callbacks() -> None:
    r = _sample_read()
    kb = cockpit_queue_keyboard("en", r, queue_code="marketing_review")
    for row in kb.export():
        for btn in row:
            assert btn.callback_data is not None
            assert "ac:c:" in btn.callback_data or btn.callback_data.startswith("ac:rq:") or btn.callback_data == "ac:h"


def test_card_callback_roundtrip() -> None:
    cb = cockpit_card_callback("marketing_review", "supplier_offer", 99)
    parsed = parse_cockpit_card_callback(cb)
    assert parsed == ("marketing_review", "supplier_offer", 99)


def test_find_card_in_cockpit() -> None:
    r = _sample_read()
    c = find_card_in_cockpit(r, queue_code="marketing_review", source_type="supplier_offer", source_id=42)
    assert c is not None
    assert c.title == "Test Offer"


def test_outbox_save_callback_toast_new_vs_replay() -> None:
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.bot.automation_cockpit_telegram import cockpit_outbox_save_callback
    from app.bot.handlers.automation_cockpit_admin import cb_cockpit_clarification_outbox_save
    from app.schemas.supplier_clarification_outbox import SupplierClarificationOutboxItemRead
    from app.services.supplier_clarification_outbox_service import (
        SupplierClarificationOutboxService,
        SupplierClarificationOutboxUpsertResult,
    )

    draft = SupplierClarificationDraftRead(supplier_offer_id=7, supplier_facing_asks=["q"])
    card = MagicMock()
    card.source_type = "supplier_offer"
    card.clarification_draft = draft
    item = SupplierClarificationOutboxItemRead(
        id=99,
        supplier_offer_id=7,
        workflow_status="draft",
        draft_snapshot={},
        created_by_telegram_user_id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async def run_once(*, replayed: bool, language: str, expected_substr: str) -> None:
        query = MagicMock()
        query.from_user = MagicMock()
        query.from_user.id = 1
        query.from_user.language_code = language
        query.data = cockpit_outbox_save_callback("marketing_review", "supplier_offer", 7)
        query.answer = AsyncMock()
        result = SupplierClarificationOutboxUpsertResult(item=item, replayed_existing=replayed)

        with (
            patch("app.bot.handlers.automation_cockpit_admin._is_admin_allowed", return_value=True),
            patch(
                "app.bot.handlers.automation_cockpit_admin._resolve_language",
                new_callable=AsyncMock,
                return_value=language,
            ),
            patch(
                "app.bot.handlers.automation_cockpit_admin._deny_if_not_allowed",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch("app.bot.handlers.automation_cockpit_admin._load_card_read", return_value=MagicMock()),
            patch(
                "app.bot.handlers.automation_cockpit_admin.find_cockpit_card_for_clarification_outbox",
                return_value=card,
            ),
            patch("app.bot.handlers.automation_cockpit_admin.SessionLocal") as SL,
            patch.object(
                SupplierClarificationOutboxService,
                "upsert_from_draft",
                return_value=result,
            ),
        ):
            cm = MagicMock()
            cm.__enter__.return_value = MagicMock()
            cm.__exit__.return_value = None
            SL.return_value = cm
            await cb_cockpit_clarification_outbox_save(query)

        query.answer.assert_called_once()
        toast = query.answer.call_args[0][0]
        assert expected_substr in toast

    asyncio.run(run_once(replayed=False, language="ro", expected_substr="Ciornă salvată"))
    asyncio.run(run_once(replayed=True, language="ro", expected_substr="Există deja"))
    asyncio.run(run_once(replayed=False, language="en", expected_substr="Draft saved"))
    asyncio.run(run_once(replayed=True, language="en", expected_substr="active draft"))
