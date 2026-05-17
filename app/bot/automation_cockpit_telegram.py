"""A1V–A1V4: format Automation Cockpit read models for Telegram admin (read-only; no mutations)."""

from __future__ import annotations

import re

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_CLOSE,
    ADMIN_AUTOMATION_COCKPIT_HOME,
    ADMIN_AUTOMATION_COCKPIT_OUTBOX_LIST_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_OUTBOX_SAVE_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_REFRESH,
    ADMIN_AUTOMATION_COCKPIT_REFRESH_QUEUE_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_SAFETY_DETAIL,
)
from app.bot.messages import translate
from app.schemas.admin_automation_cockpit import (
    AUTOMATION_COCKPIT_QUEUE_CODES,
    AdminAutomationCockpitCardRead,
    AdminAutomationCockpitRead,
)
from app.schemas.supplier_clarification_outbox import SupplierClarificationOutboxItemRead

_COCKPIT_QUEUE_ABBR: dict[str, str] = {
    "supplier_intake": "si",
    "missing_info": "mi",
    "offer_readiness": "or",
    "risk_conflict": "rc",
    "marketing_review": "mr",
    "publishing_queue": "pq",
    "catalog_conversion": "cc",
}
_COCKPIT_QUEUE_ABBR_REV: dict[str, str] = {v: k for k, v in _COCKPIT_QUEUE_ABBR.items()}

SOURCE_TYPE_ABBR: dict[str, str] = {
    "supplier_offer": "so",
    "tour": "tu",
}
SOURCE_TYPE_ABBR_REV: dict[str, str] = {v: k for k, v in SOURCE_TYPE_ABBR.items()}

_QUEUE_BTN_MESSAGE_KEY: dict[str, str] = {
    "supplier_intake": "admin_automation_cockpit_btn_supplier_intake",
    "missing_info": "admin_automation_cockpit_btn_missing_info",
    "offer_readiness": "admin_automation_cockpit_btn_offer_readiness",
    "risk_conflict": "admin_automation_cockpit_btn_risk",
    "marketing_review": "admin_automation_cockpit_btn_marketing",
    "publishing_queue": "admin_automation_cockpit_btn_publishing",
    "catalog_conversion": "admin_automation_cockpit_btn_catalog",
}

# List view: map backend next_best_action_code -> messages.py key suffix (admin_automation_cockpit_action_<key>)
_COCKPIT_LIST_ACTION_KEYS: dict[str, str] = {
    "review_missing_marketing_data": "review_missing_marketing_data",
    "review_template": "review_template",
    "open_marketing_review": "open_marketing_review",
    "open_preview": "open_preview",
    "future_edit_marketing_copy": "future_edit_marketing_copy",
    "review_conversion_health": "review_conversion_health",
    "review_already_published": "review_already_published",
    "review_publish_readiness": "review_publish_readiness",
    "resolve_publish_blocker": "resolve_publish_blocker",
    "await_publish_go_no_go": "await_publish_go_no_go",
    "future_confirm_publish": "future_confirm_publish",
    "review_catalog_visibility": "review_catalog_visibility",
    "open_prepare_chain_plan": "open_prepare_chain_plan",
    "run_conversion_dry_run_future": "run_conversion_dry_run_future",
    "resolve_conversion_blocker": "resolve_conversion_blocker",
    "review_conversion_context": "review_conversion_context",
    "review_publishing_context": "review_publishing_context",
    "guarded_internal_action": "guarded_internal_action",
    "future_capability": "future_capability",
    "safe_read": "safe_read",
    "prepare_conversion_chain": "prepare_conversion_chain",
    "create_execution_link": "create_execution_link",
    "manual_publish_available": "manual_publish_available",
    "review_warnings": "review_warnings",
    "not_applicable": "not_applicable",
    "resolve_publish_blockers": "resolve_publish_blockers",
    "review_package_refresh": "review_package_refresh",
    "open_tour_admin": "open_tour_admin",
    "verify_mini_app_catalog": "verify_mini_app_catalog",
    "open_promotion_context": "open_promotion_context",
    "review_tour_promotion_readiness": "review_tour_promotion_readiness",
    "review_catalog_promotion_health": "review_catalog_promotion_health",
    "review_conversion_after_publish": "review_conversion_after_publish",
}

_DETAIL_TITLE_MAX = 120
_DETAIL_NOTE_MAX = 320

_SOURCE_PATH_ORDER: tuple[str, ...] = (
    "admin_tour_path",
    "admin_action_path",
    "review_package_path",
    "publishing_console_detail_path",
    "publishing_console_editor_path",
    "prepare_conversion_chain_plan_path",
    "preview_path",
)
_SOURCE_PATH_LABEL_KEY: dict[str, str] = {
    "admin_tour_path": "admin_automation_cockpit_detail_src_admin_tour",
    "admin_action_path": "admin_automation_cockpit_detail_src_admin_action",
    "review_package_path": "admin_automation_cockpit_detail_src_review_package",
    "publishing_console_detail_path": "admin_automation_cockpit_detail_src_console_detail",
    "publishing_console_editor_path": "admin_automation_cockpit_detail_src_console_editor",
    "prepare_conversion_chain_plan_path": "admin_automation_cockpit_detail_src_conversion_plan",
    "preview_path": "admin_automation_cockpit_detail_src_preview",
}

_LIST_CARD_TITLE_MAX = 72
_LIST_CARD_ISSUE_MAX = 100


def cockpit_queue_heading(language_code: str | None, queue_code: str) -> str:
    key = _QUEUE_BTN_MESSAGE_KEY[queue_code]
    return translate(language_code, key)


def _open_card_button_key(source_type: str) -> str:
    if source_type == "tour":
        return "admin_automation_cockpit_open_tour_btn"
    return "admin_automation_cockpit_open_offer_btn"


def cockpit_open_card_label(language_code: str | None, *, source_type: str, source_id: int) -> str:
    return translate(language_code, _open_card_button_key(source_type), sid=str(source_id))


def _card_source_caption(language_code: str | None, *, source_type: str, source_id: int) -> str:
    if source_type == "tour":
        return translate(language_code, "admin_automation_cockpit_card_source_tour", sid=str(source_id))
    return translate(language_code, "admin_automation_cockpit_card_source_offer", sid=str(source_id))


def _snippet(text: str | None, *, max_len: int) -> str:
    t = (text or "").strip()
    if not t:
        return "—"
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


_HUMANIZE_RULES: tuple[tuple[str, str], ...] = (
    ("media_review_replacement", "admin_automation_cockpit_human_media_replace"),
    ("create_tour_bridge", "admin_automation_cockpit_human_tour_bridge"),
    ("prepare_chain", "admin_automation_cockpit_human_prepare_chain"),
    ("prepare_conversion", "admin_automation_cockpit_human_prepare_chain"),
    ("offer_debug", "admin_automation_cockpit_human_offer_state"),
    ("flags_publish_not_ready", "admin_automation_cockpit_human_not_publish_ready"),
    ("publish_readiness", "admin_automation_cockpit_human_publish_ready"),
    ("content_quality", "admin_automation_cockpit_human_content_quality"),
    ("description_thin", "admin_automation_cockpit_human_description_thin"),
    ("orphan_promo", "admin_automation_cockpit_human_promo"),
    ("cta_safety", "admin_automation_cockpit_human_cta_safety"),
    ("missing_execution", "admin_automation_cockpit_human_exec_link"),
    ("execution link", "admin_automation_cockpit_human_execution_link"),
    ("showcase_media", "admin_automation_cockpit_human_gate_media"),
    ("showcase_preview", "admin_automation_cockpit_human_gate_preview"),
    ("gate:", "admin_automation_cockpit_human_gate_generic"),
    ("publish_safe", "admin_automation_cockpit_human_publish_safe"),
    ("ineligible", "admin_automation_cockpit_human_ineligible"),
    ("conversion_target", "admin_automation_cockpit_human_conversion"),
    ("console_primary_blocker", "admin_automation_cockpit_human_console_blocked"),
    ("console_blocked", "admin_automation_cockpit_human_console_blocked"),
    ("preview_payload", "admin_automation_cockpit_human_generic_internal"),
    ("catalog gate", "admin_automation_cockpit_human_generic_internal"),
    ("mini app", "admin_automation_cockpit_human_cta_safety"),
    ("mini_app", "admin_automation_cockpit_human_cta_safety"),
)


def _detail_line_is_technical(tl: str) -> bool:
    if "[" in tl and "]" in tl and re.search(r"\[[a-z0-9_]+\]", tl):
        return True
    if re.search(r"\b[b](7|10|11|15)\b", tl):
        return True
    if re.search(r"\b[a-z]{2,}_[a-z][a-z0-9_]*", tl):
        return True
    if re.search(r"\b[a-z][a-z0-9_]*:[a-z0-9_:-]{2,}", tl):
        return True
    return False


def _strip_admin_debug_suffixes(text: str) -> str:
    """Remove parenthetical debug hints (e.g. routing codes, 'does not send') from admin-facing copy."""
    s = (text or "").strip()
    if not s:
        return ""
    s = re.sub(r"\s*\([^)]*does\s+not\s+send[^)]*\)", "", s, flags=re.I)
    s = re.sub(r"\s*\([^)]*\bB1[0-9][A-Z0-9.]*\b[^)]*\)", "", s, flags=re.I)
    return s.strip()


# Order matters: more specific needles first. Keys must exist for EN and RO in messages.py.
_ADMIN_CANNED_PHRASES: tuple[tuple[str, str], ...] = (
    ("ambiguous or non-standard publishing-console posture", "admin_automation_cockpit_risk_ro_ambiguous_posture"),
    ("tour promotion rows are not evaluated", "admin_automation_cockpit_risk_ro_tour_promo_unevaluated"),
    ("publish readiness flagged for manual review", "admin_automation_cockpit_risk_ro_publish_manual"),
    ("not ideal for catalog promotion", "admin_automation_cockpit_admin_phrase_catalog_gates"),
    ("until gates pass", "admin_automation_cockpit_admin_phrase_catalog_gates"),
    ("departure is in the past", "admin_automation_cockpit_admin_phrase_departure_past"),
    ("candidate for tour promotion", "admin_automation_cockpit_admin_phrase_tour_promo_last_seats"),
    ("last-seats style", "admin_automation_cockpit_admin_phrase_tour_promo_last_seats"),
    ("last seats style", "admin_automation_cockpit_admin_phrase_tour_promo_last_seats"),
    ("cta safety:", "admin_automation_cockpit_risk_ro_cta_generic"),
)


def humanize_admin_text(language_code: str | None, raw: str | None) -> str:
    """Cross-module humanization for admin Telegram UI (cockpit, operator workflow, panels)."""
    t = _strip_admin_debug_suffixes(raw or "")
    if not t:
        return ""
    tl = t.lower()
    for needle, msg_key in _ADMIN_CANNED_PHRASES:
        if needle in tl:
            return translate(language_code, msg_key)
    for needle, msg_key in _HUMANIZE_RULES:
        if needle in tl:
            return translate(language_code, msg_key)
    if _detail_line_is_technical(tl):
        return translate(language_code, "admin_ui_human_technical_unknown")
    return t


def _humanize_admin_blocker(language_code: str | None, raw: str | None) -> str:
    return humanize_admin_text(language_code, raw)


def _humanize_admin_warning(language_code: str | None, raw: str | None) -> str:
    return humanize_admin_text(language_code, raw)


def _humanize_admin_task(language_code: str | None, raw: str | None) -> str:
    return humanize_admin_text(language_code, raw)


def _detail_body_note(language_code: str | None, text: str | None, *, max_len: int = _DETAIL_NOTE_MAX) -> str:
    t = (text or "").strip()
    if not t:
        return "—"
    return _snippet(humanize_admin_text(language_code, t), max_len=max_len)


def _humanize_intake_headline_for_admin(language_code: str | None, headline: str | None) -> str:
    h = (headline or "").strip()
    if not h:
        return translate(language_code, "admin_automation_cockpit_human_headline_generic")
    out: list[str] = []
    for part in re.split(r"\s*;\s*", h):
        p = part.strip().lower()
        if not p:
            continue
        if p.startswith("missing:"):
            out.append(translate(language_code, "admin_automation_cockpit_human_headline_missing"))
        elif "publication blocked" in p:
            out.append(translate(language_code, "admin_automation_cockpit_human_headline_pub_blocked"))
        elif "conversion not green" in p:
            out.append(translate(language_code, "admin_automation_cockpit_human_headline_conversion"))
        elif "needs polish" in p:
            out.append(translate(language_code, "admin_automation_cockpit_human_headline_polish"))
        elif "sufficient" in p and "granularity" in p:
            out.append(translate(language_code, "admin_automation_cockpit_human_headline_ok"))
        elif _detail_line_is_technical(p):
            continue
        else:
            out.append(part.strip())
    if not out:
        return translate(language_code, "admin_automation_cockpit_human_headline_generic")
    dedup: list[str] = []
    for s in out:
        if s not in dedup:
            dedup.append(s)
    return " ".join(dedup)


def _humanize_cc_status_token(language_code: str | None, raw: str | None) -> str:
    v = (raw or "").strip()
    if not v or v in ("—", "unknown", "none", "not_applicable"):
        return ""
    vl = v.lower()
    if "block" in vl:
        return translate(language_code, "admin_automation_cockpit_cc_value_blocked")
    if "ready" in vl or "suggest" in vl:
        return translate(language_code, "admin_automation_cockpit_cc_value_ready")
    if "review" in vl or "attention" in vl or "pending" in vl:
        return translate(language_code, "admin_automation_cockpit_cc_value_needs_review")
    if _detail_line_is_technical(vl):
        return translate(language_code, "admin_automation_cockpit_cc_value_unknown")
    if len(v) > 40:
        return translate(language_code, "admin_automation_cockpit_cc_value_unknown")
    return v


def _commercial_context_a3c_lines(language_code: str | None, ctx: object) -> list[str]:
    """Human-readable commercial rows; skips empty/placeholder values."""
    rows: list[str] = []
    tour_code = getattr(ctx, "tour_code", None)
    tc = (str(tour_code).strip() if tour_code is not None else "")
    if tc and tc not in ("—", "none", "unknown"):
        rows.append(
            translate(language_code, "admin_automation_cockpit_cc_tour_code", v=tc),
        )

    for accessor, label_key in (
        ("publish_status", "admin_automation_cockpit_cc_publish"),
        ("preview_status", "admin_automation_cockpit_cc_preview"),
        ("payload_status", "admin_automation_cockpit_cc_payload"),
    ):
        val = getattr(ctx, accessor, None)
        hum = _humanize_cc_status_token(language_code, str(val) if val is not None else None)
        if hum:
            rows.append(translate(language_code, label_key, v=hum))

    tf = getattr(ctx, "template_family", None)
    tfs = (str(tf).strip() if tf is not None else "")
    if tfs and tfs.lower() not in ("unknown", "none", "not_applicable", "—", ""):
        if not _detail_line_is_technical(tfs.lower()):
            rows.append(
                translate(language_code, "admin_automation_cockpit_cc_template_family", v=tfs),
            )

    sid = getattr(ctx, "supplier_offer_id", None)
    for attr, label_msg in (
        ("already_published", "admin_automation_cockpit_cc_already_published"),
        ("has_tour_bridge", "admin_automation_cockpit_cc_bridge"),
        ("has_catalog_visible_tour", "admin_automation_cockpit_cc_catalog_visible"),
        ("has_active_execution_link", "admin_automation_cockpit_cc_exec_link"),
    ):
        bit = getattr(ctx, attr, None)
        if bit is True:
            rows.append(
                translate(
                    language_code,
                    "admin_automation_cockpit_cc_flag",
                    label=translate(language_code, label_msg),
                    v=translate(language_code, "admin_automation_cockpit_cc_bool_yes"),
                ),
            )
        elif bit is False and attr == "has_active_execution_link" and sid is not None:
            rows.append(
                translate(
                    language_code,
                    "admin_automation_cockpit_cc_flag",
                    label=translate(language_code, label_msg),
                    v=translate(language_code, "admin_automation_cockpit_cc_bool_no"),
                ),
            )

    return rows[:6]


def _format_card_detail_safety_compact(language_code: str | None) -> list[str]:
    return [
        translate(language_code, "admin_automation_cockpit_detail_safety_readonly"),
        translate(language_code, "admin_automation_cockpit_detail_safety_no_telegram_publish"),
        translate(language_code, "admin_automation_cockpit_detail_safety_no_supplier_notif"),
        translate(language_code, "admin_automation_cockpit_detail_safety_no_booking"),
    ]


def _format_detail_source_bullets(language_code: str | None, paths: dict[str, str]) -> list[str]:
    rows: list[str] = []
    for key in _SOURCE_PATH_ORDER:
        if key not in paths:
            continue
        val = str(paths.get(key) or "").strip()
        label_key = _SOURCE_PATH_LABEL_KEY.get(key)
        if label_key is None:
            continue
        label = translate(language_code, label_key)
        if val:
            state = translate(language_code, "admin_automation_cockpit_detail_link_available")
        else:
            state = translate(language_code, "admin_automation_cockpit_detail_link_missing")
        rows.append(translate(language_code, "admin_automation_cockpit_detail_src_bullet", label=label, state=state))
    return rows


def _format_card_detail_safety_human(language_code: str | None) -> list[str]:
    keys = (
        "admin_automation_cockpit_detail_safety_readonly",
        "admin_automation_cockpit_detail_safety_no_telegram_publish",
        "admin_automation_cockpit_detail_safety_no_scheduler",
        "admin_automation_cockpit_detail_safety_no_supplier_notif",
        "admin_automation_cockpit_detail_safety_no_booking",
        "admin_automation_cockpit_detail_safety_no_b11",
    )
    return [translate(language_code, k) for k in keys]


def _cc_bool_phrase(language_code: str | None, v: bool | None) -> str:
    if v is None:
        return "—"
    return translate(
        language_code,
        "admin_automation_cockpit_cc_bool_yes" if v else "admin_automation_cockpit_cc_bool_no",
    )


def _list_console_status_message_key(card: AdminAutomationCockpitCardRead) -> str:
    meta = card.metadata or {}
    cs = str(meta.get("console_status") or card.status or "").strip().lower()
    if cs == "blocked":
        return "admin_automation_cockpit_list_console_blocked"
    if cs == "needs_attention":
        return "admin_automation_cockpit_list_console_needs_attention"
    if cs == "ready":
        return "admin_automation_cockpit_list_console_ready"
    tone = str(card.status_tone or "neutral").lower()
    if tone == "danger":
        return "admin_automation_cockpit_list_console_blocked"
    if tone in ("warning",):
        return "admin_automation_cockpit_list_console_needs_attention"
    if tone in ("success",):
        return "admin_automation_cockpit_list_console_ready"
    return "admin_automation_cockpit_list_console_neutral"


def _list_next_step_line(language_code: str | None, card: AdminAutomationCockpitCardRead) -> str:
    code = (card.next_best_action_code or "").strip()
    mid = _COCKPIT_LIST_ACTION_KEYS.get(code)
    if mid:
        return translate(language_code, f"admin_automation_cockpit_action_{mid}")
    if language_code == "ro":
        return translate(language_code, "admin_automation_cockpit_list_next_see_detail")
    raw = _snippet(card.next_best_action_label, max_len=100)
    if raw != "—":
        return raw
    return translate(language_code, "admin_automation_cockpit_list_next_see_detail")


def _list_issue_line(language_code: str | None, card: AdminAutomationCockpitCardRead) -> str | None:
    blocker = (card.blocker_summary or "").strip()
    warning = (card.warning_summary or "").strip()
    if blocker:
        hb = _humanize_admin_blocker(language_code, blocker)
        if not hb:
            return None
        return translate(
            language_code,
            "admin_automation_cockpit_queue_card_blocker",
            text=_snippet(hb, max_len=_LIST_CARD_ISSUE_MAX),
        )
    if warning:
        hw = _humanize_admin_warning(language_code, warning)
        if not hw:
            return None
        return translate(
            language_code,
            "admin_automation_cockpit_queue_card_warning",
            text=_snippet(hw, max_len=_LIST_CARD_ISSUE_MAX),
        )
    return None


def _format_queue_list_card(language_code: str | None, index: int, card: AdminAutomationCockpitCardRead) -> str:
    title = _snippet(card.title, max_len=_LIST_CARD_TITLE_MAX)
    source = _card_source_caption(language_code, source_type=card.source_type, source_id=card.source_id)
    status_phrase = translate(language_code, _list_console_status_message_key(card))
    lines = [
        translate(language_code, "admin_automation_cockpit_queue_card_l1", n=str(index), title=title),
        translate(
            language_code,
            "admin_automation_cockpit_queue_card_l2",
            source=source,
            status=status_phrase,
        ),
        translate(
            language_code,
            "admin_automation_cockpit_queue_card_l3",
            step=_list_next_step_line(language_code, card),
        ),
    ]
    issue = _list_issue_line(language_code, card)
    if issue:
        lines.append(issue)
    return "\n".join(lines)


def cockpit_queue_abbrev(queue_code: str) -> str:
    return _COCKPIT_QUEUE_ABBR[queue_code]


def cockpit_queue_from_abbrev(abbrev: str) -> str | None:
    return _COCKPIT_QUEUE_ABBR_REV.get(abbrev)


def cockpit_card_callback(queue_code: str, source_type: str, source_id: int) -> str:
    q = _COCKPIT_QUEUE_ABBR[queue_code]
    st = SOURCE_TYPE_ABBR.get(source_type, source_type[:2])
    return f"{ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX}{q}:{st}:{source_id}"


def parse_cockpit_card_callback(data: str) -> tuple[str, str, int] | None:
    """Return (queue_code, source_type, source_id) or None."""
    if not data.startswith(ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX):
        return None
    rest = data.removeprefix(ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX)
    parts = rest.split(":")
    if len(parts) != 3:
        return None
    q_abbrev, st_abbrev, sid_s = parts
    q = cockpit_queue_from_abbrev(q_abbrev)
    st = SOURCE_TYPE_ABBR_REV.get(st_abbrev)
    if q is None or st is None:
        return None
    try:
        sid = int(sid_s)
    except ValueError:
        return None
    return q, st, sid


def find_card_in_cockpit(
    read: AdminAutomationCockpitRead,
    *,
    queue_code: str,
    source_type: str,
    source_id: int,
) -> AdminAutomationCockpitCardRead | None:
    for q in read.queues:
        if q.queue_code != queue_code:
            continue
        for card in q.cards:
            if card.source_type == source_type and card.source_id == source_id:
                return card
    return None


def cockpit_clarification_outbox_save_eligible(card: AdminAutomationCockpitCardRead | None) -> bool:
    if card is None or card.source_type != "supplier_offer":
        return False
    cd = card.clarification_draft
    if cd is None:
        return False
    return bool(cd.supplier_facing_message_ro or cd.supplier_facing_asks or cd.internal_admin_tasks)


def cockpit_outbox_save_callback(queue_code: str, source_type: str, source_id: int) -> str:
    q = _COCKPIT_QUEUE_ABBR[queue_code]
    st = SOURCE_TYPE_ABBR.get(source_type, source_type[:2])
    return f"{ADMIN_AUTOMATION_COCKPIT_OUTBOX_SAVE_PREFIX}{q}:{st}:{source_id}"


def cockpit_outbox_list_callback(queue_code: str, source_type: str, source_id: int) -> str:
    q = _COCKPIT_QUEUE_ABBR[queue_code]
    st = SOURCE_TYPE_ABBR.get(source_type, source_type[:2])
    return f"{ADMIN_AUTOMATION_COCKPIT_OUTBOX_LIST_PREFIX}{q}:{st}:{source_id}"


def _parse_cockpit_outbox_triplet(prefix: str, data: str) -> tuple[str, str, int] | None:
    if not data.startswith(prefix):
        return None
    rest = data.removeprefix(prefix)
    parts = rest.split(":")
    if len(parts) != 3:
        return None
    q_abbrev, st_abbrev, sid_s = parts
    q = cockpit_queue_from_abbrev(q_abbrev)
    st = SOURCE_TYPE_ABBR_REV.get(st_abbrev)
    if q is None or st is None:
        return None
    try:
        sid = int(sid_s)
    except ValueError:
        return None
    return q, st, sid


def parse_cockpit_outbox_save_callback(data: str) -> tuple[str, str, int] | None:
    return _parse_cockpit_outbox_triplet(ADMIN_AUTOMATION_COCKPIT_OUTBOX_SAVE_PREFIX, data)


def parse_cockpit_outbox_list_callback(data: str) -> tuple[str, str, int] | None:
    return _parse_cockpit_outbox_triplet(ADMIN_AUTOMATION_COCKPIT_OUTBOX_LIST_PREFIX, data)


def format_cockpit_clarification_outbox_list_text(
    language_code: str | None,
    *,
    supplier_offer_id: int,
    items: list[SupplierClarificationOutboxItemRead],
) -> str:
    header = translate(language_code, "admin_automation_cockpit_outbox_list_header", sid=str(supplier_offer_id))
    if not items:
        return "\n".join([header, "", translate(language_code, "admin_automation_cockpit_outbox_list_empty")])
    lines: list[str] = [header, ""]
    for it in items[:15]:
        lines.append(
            translate(
                language_code,
                "admin_automation_cockpit_outbox_list_line",
                oid=str(it.id),
                status=it.workflow_status,
                created=it.created_at.isoformat(timespec="seconds"),
            )
        )
    lines.extend(["", translate(language_code, "admin_automation_cockpit_outbox_list_footer")])
    return "\n".join(lines)


def cockpit_outbox_list_back_keyboard(
    language_code: str | None,
    *,
    card_refresh_callback: str,
) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_outbox_back_to_card"),
        callback_data=card_refresh_callback,
    )
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_back_home"), callback_data=ADMIN_AUTOMATION_COCKPIT_HOME)
    kb.adjust(1)
    return kb


def format_cockpit_summary_text(language_code: str | None, read: AdminAutomationCockpitRead) -> str:
    s = read.summary
    qc = s.queue_counts
    lines = [
        translate(language_code, "admin_automation_cockpit_title"),
        "",
        translate(language_code, "admin_automation_cockpit_summary_total", total=str(s.total_cards)),
        translate(language_code, "admin_automation_cockpit_summary_urgent", n=str(s.urgent_count)),
        translate(language_code, "admin_automation_cockpit_summary_needs_attention", n=str(s.needs_attention_count)),
        translate(language_code, "admin_automation_cockpit_summary_ready", n=str(s.ready_count)),
        translate(language_code, "admin_automation_cockpit_summary_blocked", n=str(s.blocked_count)),
        translate(language_code, "admin_automation_cockpit_summary_future_disabled", n=str(s.future_disabled_count)),
        "",
        translate(language_code, "admin_automation_cockpit_queue_counts_header"),
    ]
    for qcode in AUTOMATION_COCKPIT_QUEUE_CODES:
        label = translate(language_code, _QUEUE_BTN_MESSAGE_KEY[qcode])
        lines.append(f"{label}: {qc.get(qcode, 0)}")
    lines.extend(
        [
            "",
            translate(language_code, "admin_automation_cockpit_safety_compact"),
            "",
            translate(language_code, "admin_automation_cockpit_fact_lock_short"),
        ]
    )
    return "\n".join(lines)


def format_cockpit_safety_detail_text(language_code: str | None, read: AdminAutomationCockpitRead) -> str:
    ss = read.safety_summary
    return "\n".join(
        [
            translate(language_code, "admin_automation_cockpit_safety_detail_title"),
            "",
            translate(
                language_code,
                "admin_automation_cockpit_safety_lines",
                ro=str(ss.read_only),
                nt=str(ss.no_telegram_io),
                np=str(ss.no_publish_attempt),
                ns=str(ss.no_scheduler),
                nn=str(ss.no_supplier_notification_send),
                nq=str(ss.no_qr_token),
                nl=str(ss.no_layer_a_mutation),
                nb=str(ss.no_b11_change),
            ),
        ]
    )


def format_cockpit_queue_text(
    language_code: str | None,
    read: AdminAutomationCockpitRead,
    *,
    queue_code: str,
) -> str:
    qrow = next((q for q in read.queues if q.queue_code == queue_code), None)
    if qrow is None:
        return translate(language_code, "admin_automation_cockpit_queue_missing")
    heading = cockpit_queue_heading(language_code, queue_code)
    lines = [
        heading,
        "",
        translate(language_code, "admin_automation_cockpit_queue_lane_note"),
        "",
        translate(language_code, "admin_automation_cockpit_queue_total", total=str(qrow.total_count)),
        "",
    ]
    if not qrow.cards:
        lines.append(translate(language_code, "admin_automation_cockpit_queue_no_cards"))
        return "\n".join(lines)
    lines.append(translate(language_code, "admin_automation_cockpit_queue_cards_header"))
    for i, c in enumerate(qrow.cards[:5], start=1):
        lines.append(_format_queue_list_card(language_code, i, c))
    return "\n".join(lines)


def format_cockpit_card_detail_text(language_code: str | None, card: AdminAutomationCockpitCardRead) -> str:
    title = _snippet(card.title, max_len=_DETAIL_TITLE_MAX)
    source = _card_source_caption(language_code, source_type=card.source_type, source_id=card.source_id)
    status_phrase = translate(language_code, _list_console_status_message_key(card))

    lines: list[str] = [
        translate(language_code, "admin_automation_cockpit_card_detail_header"),
        "",
        title,
        translate(
            language_code,
            "admin_automation_cockpit_queue_card_l2",
            source=source,
            status=status_phrase,
        ),
    ]

    blocker = (card.blocker_summary or "").strip()
    hb = _humanize_admin_blocker(language_code, blocker) if blocker else ""
    if hb:
        lines.extend(["", translate(language_code, "admin_automation_cockpit_detail_a3c_main_blocker"), hb])

    warn_bits: list[str] = []
    if (card.warning_summary or "").strip():
        w = _humanize_admin_warning(language_code, card.warning_summary)
        if w:
            warn_bits.append(w)
    if (card.risk_summary or "").strip():
        r = _humanize_admin_warning(language_code, card.risk_summary)
        if r:
            warn_bits.append(r)
    if warn_bits:
        lines.extend(
            [
                "",
                translate(language_code, "admin_automation_cockpit_detail_warning_section"),
                " ".join(warn_bits),
            ]
        )

    iv = card.intake_validation
    if iv is not None:
        lines.extend(
            [
                "",
                translate(language_code, "admin_automation_cockpit_detail_a3c_validation"),
                _humanize_intake_headline_for_admin(language_code, iv.headline),
            ]
        )

    lines.extend(
        [
            "",
            translate(language_code, "admin_automation_cockpit_detail_step_section"),
            _list_next_step_line(language_code, card),
        ]
    )

    cd = card.clarification_draft
    if cd is not None and (cd.supplier_facing_message_ro or cd.supplier_facing_asks):
        lines.append("")
        lines.append(translate(language_code, "admin_automation_cockpit_detail_a3c_supplier"))
        if cd.supplier_facing_message_ro:
            msg = (cd.supplier_facing_message_ro or "").strip()
            if len(msg) > 3500:
                msg = msg[:3497].rstrip() + "…"
            lines.append(msg)
        else:
            for x in cd.supplier_facing_asks[:5]:
                lines.append(f"• {x}")

    if cd is not None and cd.internal_admin_tasks:
        lines.append("")
        lines.append(translate(language_code, "admin_automation_cockpit_detail_a3c_internal"))
        seen_human: set[str] = set()
        humanized_unique: list[str] = []
        for x in cd.internal_admin_tasks:
            h = _humanize_admin_task(language_code, x)
            if not h or h in seen_human:
                continue
            seen_human.add(h)
            humanized_unique.append(h)
        _internal_cap = 5
        for h in humanized_unique[:_internal_cap]:
            lines.append(f"• {h}")
        if len(humanized_unique) > _internal_cap:
            lines.append(translate(language_code, "admin_automation_cockpit_detail_internal_tasks_overflow"))

    owner = (card.owner_role or "").strip()
    if owner and owner != "admin_operator":
        lines.extend(
            [
                "",
                translate(
                    language_code,
                    "admin_automation_cockpit_detail_owner_line",
                    text=owner,
                ),
            ]
        )

    if card.commercial_context is not None:
        ctx = card.commercial_context
        crows = _commercial_context_a3c_lines(language_code, ctx)
        lines.append("")
        lines.append(translate(language_code, "admin_automation_cockpit_detail_a3c_commercial"))
        if crows:
            lines.extend(crows)
        lines.extend(
            [
                "",
                translate(language_code, "admin_automation_cockpit_detail_fact_lock_header"),
                translate(language_code, "admin_automation_cockpit_fact_lock_card_detail"),
            ]
        )

    lines.extend(
        [
            "",
            translate(language_code, "admin_automation_cockpit_detail_safety_header"),
            *_format_card_detail_safety_compact(language_code),
        ]
    )
    return "\n".join(lines)


def cockpit_safety_detail_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_back_home"), callback_data=ADMIN_AUTOMATION_COCKPIT_HOME)
    kb.adjust(1)
    return kb


def cockpit_summary_keyboard(language_code: str | None) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_supplier_intake"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{cockpit_queue_abbrev('supplier_intake')}",
    )
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_missing_info"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{cockpit_queue_abbrev('missing_info')}",
    )
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_offer_readiness"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{cockpit_queue_abbrev('offer_readiness')}",
    )
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_risk"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{cockpit_queue_abbrev('risk_conflict')}",
    )
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_marketing"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{cockpit_queue_abbrev('marketing_review')}",
    )
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_publishing"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{cockpit_queue_abbrev('publishing_queue')}",
    )
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_catalog"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{cockpit_queue_abbrev('catalog_conversion')}",
    )
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_safety_detail"),
        callback_data=ADMIN_AUTOMATION_COCKPIT_SAFETY_DETAIL,
    )
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_refresh"), callback_data=ADMIN_AUTOMATION_COCKPIT_REFRESH)
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_close"), callback_data=ADMIN_AUTOMATION_COCKPIT_CLOSE)
    kb.adjust(2)
    return kb


def cockpit_queue_keyboard(
    language_code: str | None,
    read: AdminAutomationCockpitRead,
    *,
    queue_code: str,
) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    qrow = next((q for q in read.queues if q.queue_code == queue_code), None)
    if qrow:
        for c in qrow.cards[:5]:
            label = cockpit_open_card_label(language_code, source_type=c.source_type, source_id=c.source_id)
            kb.button(text=label, callback_data=cockpit_card_callback(queue_code, c.source_type, c.source_id))
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_refresh"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_REFRESH_QUEUE_PREFIX}{cockpit_queue_abbrev(queue_code)}",
    )
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_back_home"), callback_data=ADMIN_AUTOMATION_COCKPIT_HOME)
    kb.adjust(1)
    return kb


def cockpit_card_keyboard(
    language_code: str | None,
    *,
    queue_code: str,
    card_refresh_callback: str,
    card: AdminAutomationCockpitCardRead | None = None,
) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    q_abbrev = cockpit_queue_abbrev(queue_code)
    if card is not None and cockpit_clarification_outbox_save_eligible(card):
        kb.button(
            text=translate(language_code, "admin_automation_cockpit_btn_clarification_save_outbox"),
            callback_data=cockpit_outbox_save_callback(queue_code, card.source_type, card.source_id),
        )
        kb.button(
            text=translate(language_code, "admin_automation_cockpit_btn_clarification_outbox_list"),
            callback_data=cockpit_outbox_list_callback(queue_code, card.source_type, card.source_id),
        )
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_back_queue"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{q_abbrev}",
    )
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_back_home"), callback_data=ADMIN_AUTOMATION_COCKPIT_HOME)
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_refresh"), callback_data=card_refresh_callback)
    kb.adjust(1)
    return kb
