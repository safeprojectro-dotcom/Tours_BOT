"""A1V: Automation Cockpit Telegram formatters and callback encoding (read-only)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.bot.automation_cockpit_telegram import (
    cockpit_card_callback,
    cockpit_queue_keyboard,
    cockpit_summary_keyboard,
    find_card_in_cockpit,
    format_cockpit_card_detail_text,
    format_cockpit_queue_text,
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


def _sample_safety_summary() -> AdminAutomationCockpitSafetySummaryRead:
    return AdminAutomationCockpitSafetySummaryRead(
        note="read-only test",
    )


def _sample_card(*, commercial: bool = False) -> AdminAutomationCockpitCardRead:
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
        source_type="supplier_offer",
        source_id=42,
        title="Test Offer",
        status="ready",
        status_label="Ready",
        status_tone="success",
        priority=1,
        next_best_action_code="noop",
        next_best_action_label="Read",
        next_best_action_kind="safe_read",
        next_best_action_enabled=True,
        blocker_summary=None,
        commercial_context=ctx,
        safety_flags=AdminAutomationCockpitCardSafetyFlagsRead(),
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


def test_format_cockpit_summary_includes_queues_and_safety() -> None:
    body = format_cockpit_summary_text("en", _sample_read())
    assert "Admin Automation Cockpit" in body
    assert "supplier_intake: 1" in body
    assert "marketing_review: 3" in body
    assert "read_only=True" in body
    assert "Supplier/catalog facts are read-only" in body


def test_format_cockpit_queue_lists_cards_and_actions() -> None:
    r = _sample_read()
    body = format_cockpit_queue_text("en", r, queue_code="marketing_review")
    assert "Marketing" in body
    assert "Test Offer" in body
    assert "safe_read" in body
    assert "next:" in body or "next:" in body.lower()


def test_format_cockpit_card_detail_commercial_and_fact_lock() -> None:
    c = _sample_card(commercial=True)
    body = format_cockpit_card_detail_text("en", c)
    assert "Commercial context" in body
    assert "FACT_LOCK_NOTE_TEST" in body
    assert "tour_code: TC1" in body


def test_cockpit_keyboards_no_publish_callbacks() -> None:
    kb = cockpit_summary_keyboard("en")
    for row in kb.export():
        for btn in row:
            assert btn.callback_data is not None
            low = btn.callback_data.lower()
            assert "publish" not in low
            assert "channel" not in low


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
