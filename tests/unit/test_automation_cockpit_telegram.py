"""A1V–A1V4: Automation Cockpit Telegram formatters and callback tests (read-only)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.bot.automation_cockpit_telegram import (
    cockpit_card_callback,
    cockpit_queue_keyboard,
    cockpit_summary_keyboard,
    find_card_in_cockpit,
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
from app.schemas.supplier_offer_intake_validation import SupplierOfferIntakeValidationRead
from app.services.supplier_clarification_draft_service import SupplierClarificationDraftService


def _sample_safety_summary() -> AdminAutomationCockpitSafetySummaryRead:
    return AdminAutomationCockpitSafetySummaryRead(
        note="read-only test",
    )


def _sample_card(
    *,
    commercial: bool = False,
    source_type: str = "supplier_offer",
    source_paths: dict[str, str] | None = None,
) -> AdminAutomationCockpitCardRead:
    ctx = (
        AdminAutomationCockpitCommercialContextRead(
            tour_code="TC1",
            fact_lock_note="FACT_LOCK_NOTE_TEST",
        )
        if commercial
        else None
    )
    return AdminAutomationCockpitCardRead(
        card_id="x",
        source_type=source_type,
        source_id=42,
        title="Test Offer",
        status="needs_attention",
        status_label="Needs attention",
        status_tone="warning",
        priority=1,
        next_best_action_code="review_missing_marketing_data",
        next_best_action_label="Review missing marketing data",
        next_best_action_kind="safe_read",
        next_best_action_enabled=True,
        blocker_summary="Package must be approved for publishing.",
        commercial_context=ctx,
        safety_flags=AdminAutomationCockpitCardSafetyFlagsRead(),
        source_paths=source_paths or {},
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
    assert "Next step:" in body
    assert "Check missing marketing data" in body
    assert "⛔" in body
    assert "Package must" in body
    assert "safe_read" not in body
    assert "kind=" not in body
    assert "Status:" not in body


def test_format_cockpit_queue_list_ro_standard_lines() -> None:
    r = _sample_read()
    body = format_cockpit_queue_text("ro", r, queue_code="marketing_review")
    assert "Următorul pas:" in body
    assert "Necesită atenție" in body
    assert "Verifică datele marketing lipsă" in body
    assert "Review missing" not in body


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
    assert "Suggested next step:" in body
    assert "Check missing marketing data" in body
    assert "Main blocker:" in body
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
    assert "Pas sugerat:" in body
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
