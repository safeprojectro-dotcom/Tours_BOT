"""A1V–A1V4: format Automation Cockpit read models for Telegram admin (read-only; no mutations)."""

from __future__ import annotations

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_CLOSE,
    ADMIN_AUTOMATION_COCKPIT_HOME,
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


def _detail_body_note(language_code: str | None, text: str | None, *, max_len: int = _DETAIL_NOTE_MAX) -> str:
    raw = _snippet(text, max_len=max_len)
    if raw == "—":
        return raw
    if language_code == "ro":
        mapped = _risk_note_ro_substitutions(raw)
        if mapped is not None:
            return mapped
    return raw


def _risk_note_ro_substitutions(text: str) -> str | None:
    """Replace frequent English risk/note sentences with Romanian catalogue text."""
    t = text.strip()
    tl = t.lower()
    pairs: list[tuple[str, str]] = [
        ("publish readiness flagged for manual review", "admin_automation_cockpit_risk_ro_publish_manual"),
        ("ambiguous or non-standard publishing-console posture", "admin_automation_cockpit_risk_ro_ambiguous_posture"),
        ("tour promotion rows are not evaluated", "admin_automation_cockpit_risk_ro_tour_promo_unevaluated"),
        ("candidate for tour promotion", "admin_automation_cockpit_risk_ro_candidate_promotion"),
    ]
    for needle, msg_key in pairs:
        if needle in tl:
            return translate("ro", msg_key)
    if "cta safety:" in tl:
        return translate("ro", "admin_automation_cockpit_risk_ro_cta_generic")
    return None


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
        return translate(
            language_code,
            "admin_automation_cockpit_queue_card_blocker",
            text=_snippet(blocker, max_len=_LIST_CARD_ISSUE_MAX),
        )
    if warning:
        return translate(
            language_code,
            "admin_automation_cockpit_queue_card_warning",
            text=_snippet(warning, max_len=_LIST_CARD_ISSUE_MAX),
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
        "",
        translate(language_code, "admin_automation_cockpit_detail_step_section"),
        _list_next_step_line(language_code, card),
    ]

    blocker = (card.blocker_summary or "").strip()
    if blocker:
        lines.extend(
            [
                "",
                translate(language_code, "admin_automation_cockpit_detail_blocker_section"),
                translate(
                    language_code,
                    "admin_automation_cockpit_detail_note_body",
                    text=_detail_body_note(language_code, blocker),
                ),
            ]
        )

    warning = (card.warning_summary or "").strip()
    if warning:
        lines.extend(
            [
                "",
                translate(language_code, "admin_automation_cockpit_detail_warning_section"),
                translate(
                    language_code,
                    "admin_automation_cockpit_detail_note_body_warn",
                    text=_detail_body_note(language_code, warning),
                ),
            ]
        )

    risk = (card.risk_summary or "").strip()
    if risk:
        lines.extend(
            [
                "",
                translate(language_code, "admin_automation_cockpit_detail_risk_section"),
                translate(
                    language_code,
                    "admin_automation_cockpit_detail_note_body_warn",
                    text=_detail_body_note(language_code, risk),
                ),
            ]
        )

    iv = card.intake_validation
    if iv is not None:
        lines.extend(
            [
                "",
                translate(language_code, "admin_automation_cockpit_detail_intake_header"),
                _snippet(iv.headline, max_len=240),
            ]
        )
        if iv.facts_missing_required:
            lines.append(translate(language_code, "admin_automation_cockpit_detail_intake_missing"))
            for x in iv.facts_missing_required[:5]:
                lines.append(f"• {_snippet(str(x), max_len=200)}")
        cd = card.clarification_draft
        if cd is not None:
            lines.extend(
                [
                    "",
                    translate(language_code, "admin_automation_cockpit_detail_clarification_header"),
                    translate(language_code, "admin_automation_cockpit_detail_clarification_draft_note"),
                ]
            )
            if cd.supplier_facing_message_ro:
                lines.append("")
                lines.append(translate(language_code, "admin_automation_cockpit_detail_clarification_supplier"))
                msg = (cd.supplier_facing_message_ro or "").strip()
                if len(msg) > 3500:
                    msg = msg[:3497].rstrip() + "…"
                lines.append(msg)
            elif cd.supplier_facing_asks:
                lines.append(translate(language_code, "admin_automation_cockpit_detail_clarification_supplier"))
                for x in cd.supplier_facing_asks[:5]:
                    lines.append(f"• {_snippet(str(x), max_len=380)}")
            if cd.internal_admin_tasks:
                lines.append("")
                lines.append(translate(language_code, "admin_automation_cockpit_detail_clarification_internal"))
                for x in cd.internal_admin_tasks[:7]:
                    lines.append(f"• {_snippet(str(x), max_len=380)}")
        lines.extend(
            [
                "",
                translate(
                    language_code,
                    "admin_automation_cockpit_detail_note_body_warn",
                    text=_detail_body_note(
                        language_code,
                        translate(language_code, "admin_automation_cockpit_detail_intake_note"),
                    ),
                ),
            ]
        )

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

    bullets = _format_detail_source_bullets(language_code, card.source_paths or {})
    if bullets:
        lines.extend(["", translate(language_code, "admin_automation_cockpit_detail_sources_section"), *bullets])

    if card.commercial_context is not None:
        ctx = card.commercial_context
        lines.extend(
            [
                "",
                translate(language_code, "admin_automation_cockpit_commercial_header"),
                translate(language_code, "admin_automation_cockpit_cc_publish", v=ctx.publish_status or "—"),
                translate(language_code, "admin_automation_cockpit_cc_preview", v=ctx.preview_status or "—"),
                translate(language_code, "admin_automation_cockpit_cc_payload", v=ctx.payload_status or "—"),
                translate(language_code, "admin_automation_cockpit_cc_template_family", v=ctx.template_family or "—"),
                translate(language_code, "admin_automation_cockpit_cc_template_id", v=ctx.selected_template_id or "—"),
                translate(language_code, "admin_automation_cockpit_cc_tour_code", v=ctx.tour_code or "—"),
                translate(
                    language_code,
                    "admin_automation_cockpit_cc_flag",
                    label=translate(language_code, "admin_automation_cockpit_cc_already_published"),
                    v=_cc_bool_phrase(language_code, ctx.already_published),
                ),
                translate(
                    language_code,
                    "admin_automation_cockpit_cc_flag",
                    label=translate(language_code, "admin_automation_cockpit_cc_bridge"),
                    v=_cc_bool_phrase(language_code, ctx.has_tour_bridge),
                ),
                translate(
                    language_code,
                    "admin_automation_cockpit_cc_flag",
                    label=translate(language_code, "admin_automation_cockpit_cc_catalog_visible"),
                    v=_cc_bool_phrase(language_code, ctx.has_catalog_visible_tour),
                ),
                translate(
                    language_code,
                    "admin_automation_cockpit_cc_flag",
                    label=translate(language_code, "admin_automation_cockpit_cc_exec_link"),
                    v=_cc_bool_phrase(language_code, ctx.has_active_execution_link),
                ),
            ]
        )
        note = (ctx.fact_lock_note or "").strip()
        if note:
            lines.extend(["", translate(language_code, "admin_automation_cockpit_detail_fact_lock_header"), note[:500]])

    lines.extend(
        [
            "",
            translate(language_code, "admin_automation_cockpit_detail_safety_header"),
            *_format_card_detail_safety_human(language_code),
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
) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    q_abbrev = cockpit_queue_abbrev(queue_code)
    kb.button(
        text=translate(language_code, "admin_automation_cockpit_btn_back_queue"),
        callback_data=f"{ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX}{q_abbrev}",
    )
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_back_home"), callback_data=ADMIN_AUTOMATION_COCKPIT_HOME)
    kb.button(text=translate(language_code, "admin_automation_cockpit_btn_refresh"), callback_data=card_refresh_callback)
    kb.adjust(1)
    return kb
