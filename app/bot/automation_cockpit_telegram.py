"""A1V / A1V2: format Automation Cockpit read models for Telegram admin (read-only; no mutations)."""

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


def _card_issues_line(language_code: str | None, *, blocker: str | None, warning: str | None) -> str | None:
    b = (blocker or "").strip()
    w = (warning or "").strip()
    if not b and not w:
        return None
    if b and w:
        return translate(language_code, "admin_automation_cockpit_card_issues_both", blocker=b, warn=w)
    if b:
        return translate(language_code, "admin_automation_cockpit_card_issues_blocker_only", blocker=b)
    return translate(language_code, "admin_automation_cockpit_card_issues_warn_only", warn=w)


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
        status_human = (c.status_label or "").strip() or c.status
        next_step = (c.next_best_action_label or "").strip() or "—"
        issues = _card_issues_line(language_code, blocker=c.blocker_summary, warning=c.warning_summary)
        block = translate(
            language_code,
            "admin_automation_cockpit_card_compact",
            n=str(i),
            title=c.title,
            source=_card_source_caption(language_code, source_type=c.source_type, source_id=c.source_id),
            status=status_human,
            next_step=next_step,
        )
        if issues:
            block = f"{block}\n{issues}"
        lines.append(block)
    return "\n".join(lines)


def _fmt_path_lines(card: AdminAutomationCockpitCardRead) -> list[str]:
    if not card.source_paths:
        return []
    return [f"{k}: {v}" for k, v in sorted(card.source_paths.items())]


def format_cockpit_card_detail_text(language_code: str | None, card: AdminAutomationCockpitCardRead) -> str:
    status_human = (card.status_label or "").strip() or card.status
    lines = [
        translate(language_code, "admin_automation_cockpit_card_detail_header"),
        "",
        f"{card.title}",
        translate(
            language_code,
            "admin_automation_cockpit_detail_source",
            caption=_card_source_caption(language_code, source_type=card.source_type, source_id=card.source_id),
        ),
        translate(
            language_code,
            "admin_automation_cockpit_detail_status",
            status=status_human,
        ),
        "",
        translate(
            language_code,
            "admin_automation_cockpit_card_next_step_only",
            label=(card.next_best_action_label or "—"),
        ),
        "",
        translate(
            language_code,
            "admin_automation_cockpit_detail_blocker",
            text=card.blocker_summary or "—",
        ),
        translate(
            language_code,
            "admin_automation_cockpit_detail_warning",
            text=card.warning_summary or "—",
        ),
        translate(
            language_code,
            "admin_automation_cockpit_detail_risk",
            text=card.risk_summary or "—",
        ),
        translate(
            language_code,
            "admin_automation_cockpit_detail_owner",
            text=card.owner_role or "—",
        ),
        "",
    ]
    pl = _fmt_path_lines(card)
    if pl:
        lines.append(translate(language_code, "admin_automation_cockpit_paths_header"))
        lines.extend(pl)
        lines.append("")
    lines.append(translate(language_code, "admin_automation_cockpit_card_safety_flags"))
    lines.append(
        translate(
            language_code,
            "admin_automation_cockpit_card_safety_lines",
            ro=str(card.safety_flags.read_only),
            nt=str(card.safety_flags.no_telegram_io),
            np=str(card.safety_flags.no_publish_attempt),
            ns=str(card.safety_flags.no_scheduler),
            nn=str(card.safety_flags.no_supplier_notification_send),
            nq=str(card.safety_flags.no_qr_token),
            nl=str(card.safety_flags.no_layer_a_mutation),
            nb=str(card.safety_flags.no_b11_change),
        )
    )
    if card.commercial_context is not None:
        ctx = card.commercial_context
        lines.append("")
        lines.append(translate(language_code, "admin_automation_cockpit_commercial_header"))
        lines.append(translate(language_code, "admin_automation_cockpit_cc_publish", v=ctx.publish_status or "—"))
        lines.append(translate(language_code, "admin_automation_cockpit_cc_preview", v=ctx.preview_status or "—"))
        lines.append(translate(language_code, "admin_automation_cockpit_cc_payload", v=ctx.payload_status or "—"))
        lines.append(translate(language_code, "admin_automation_cockpit_cc_template_family", v=ctx.template_family or "—"))
        lines.append(translate(language_code, "admin_automation_cockpit_cc_template_id", v=ctx.selected_template_id or "—"))
        lines.append(translate(language_code, "admin_automation_cockpit_cc_tour_code", v=ctx.tour_code or "—"))
        lines.append(
            translate(
                language_code,
                "admin_automation_cockpit_cc_flag",
                label=translate(language_code, "admin_automation_cockpit_cc_already_published"),
                v=str(ctx.already_published) if ctx.already_published is not None else "—",
            )
        )
        lines.append(
            translate(
                language_code,
                "admin_automation_cockpit_cc_flag",
                label=translate(language_code, "admin_automation_cockpit_cc_bridge"),
                v=str(ctx.has_tour_bridge) if ctx.has_tour_bridge is not None else "—",
            )
        )
        lines.append(
            translate(
                language_code,
                "admin_automation_cockpit_cc_flag",
                label=translate(language_code, "admin_automation_cockpit_cc_catalog_visible"),
                v=str(ctx.has_catalog_visible_tour) if ctx.has_catalog_visible_tour is not None else "—",
            )
        )
        lines.append(
            translate(
                language_code,
                "admin_automation_cockpit_cc_flag",
                label=translate(language_code, "admin_automation_cockpit_cc_exec_link"),
                v=str(ctx.has_active_execution_link) if ctx.has_active_execution_link is not None else "—",
            )
        )
        lines.append("")
        note = (ctx.fact_lock_note or "").strip()
        if note:
            lines.append(note[:500])
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
