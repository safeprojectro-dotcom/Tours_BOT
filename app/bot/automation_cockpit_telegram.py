"""A1V: format Automation Cockpit read models for Telegram admin (read-only; no mutations)."""

from __future__ import annotations

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    ADMIN_AUTOMATION_COCKPIT_CARD_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_CLOSE,
    ADMIN_AUTOMATION_COCKPIT_HOME,
    ADMIN_AUTOMATION_COCKPIT_QUEUE_PREFIX,
    ADMIN_AUTOMATION_COCKPIT_REFRESH,
    ADMIN_AUTOMATION_COCKPIT_REFRESH_QUEUE_PREFIX,
)
from app.bot.messages import translate
from app.schemas.admin_automation_cockpit import (
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

FACT_LOCK_SHORT = (
    "Supplier/catalog facts are read-only. Marketing review may change copy only, "
    "not price/route/inclusions/discounts/capacity."
)


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
        translate(
            language_code,
            "admin_automation_cockpit_summary_counts",
            total=s.total_cards,
            urgent=s.urgent_count,
            needs_attention=s.needs_attention_count,
            ready=s.ready_count,
            blocked=s.blocked_count,
            future_disabled=s.future_disabled_count,
        ),
        "",
        translate(language_code, "admin_automation_cockpit_queue_counts_header"),
        f"· supplier_intake: {qc.get('supplier_intake', 0)}",
        f"· missing_info: {qc.get('missing_info', 0)}",
        f"· offer_readiness: {qc.get('offer_readiness', 0)}",
        f"· risk_conflict: {qc.get('risk_conflict', 0)}",
        f"· marketing_review: {qc.get('marketing_review', 0)}",
        f"· publishing_queue: {qc.get('publishing_queue', 0)}",
        f"· catalog_conversion: {qc.get('catalog_conversion', 0)}",
        "",
        translate(language_code, "admin_automation_cockpit_safety_header"),
        translate(
            language_code,
            "admin_automation_cockpit_safety_lines",
            ro=str(read.safety_summary.read_only),
            nt=str(read.safety_summary.no_telegram_io),
            np=str(read.safety_summary.no_publish_attempt),
            ns=str(read.safety_summary.no_scheduler),
            nn=str(read.safety_summary.no_supplier_notification_send),
            nq=str(read.safety_summary.no_qr_token),
            nl=str(read.safety_summary.no_layer_a_mutation),
            nb=str(read.safety_summary.no_b11_change),
        ),
        "",
        FACT_LOCK_SHORT,
    ]
    return "\n".join(lines)


def format_cockpit_queue_text(
    language_code: str | None,
    read: AdminAutomationCockpitRead,
    *,
    queue_code: str,
) -> str:
    qrow = next((q for q in read.queues if q.queue_code == queue_code), None)
    if qrow is None:
        return translate(language_code, "admin_automation_cockpit_queue_missing")
    lines = [
        f"{qrow.queue_label}",
        "",
        qrow.description,
        "",
        translate(language_code, "admin_automation_cockpit_queue_total", total=qrow.total_count),
        "",
    ]
    if not qrow.cards:
        lines.append(translate(language_code, "admin_automation_cockpit_queue_no_cards"))
        return "\n".join(lines)
    lines.append(translate(language_code, "admin_automation_cockpit_queue_cards_header"))
    for i, c in enumerate(qrow.cards[:5], start=1):
        bl = c.blocker_summary or "—"
        wl = c.warning_summary or "—"
        lines.append(
            translate(
                language_code,
                "admin_automation_cockpit_card_compact",
                n=i,
                title=c.title,
                st=c.source_type,
                sid=c.source_id,
                status=c.status,
                tone=c.status_tone,
                prio=c.priority,
                act_label=c.next_best_action_label,
                act_kind=c.next_best_action_kind,
                act_en=c.next_best_action_enabled,
                blocker=bl,
                warn=wl,
            )
        )
    return "\n".join(lines)


def _fmt_path_lines(card: AdminAutomationCockpitCardRead) -> list[str]:
    if not card.source_paths:
        return []
    return [f"{k}: {v}" for k, v in sorted(card.source_paths.items())]


def format_cockpit_card_detail_text(language_code: str | None, card: AdminAutomationCockpitCardRead) -> str:
    lines = [
        translate(language_code, "admin_automation_cockpit_card_detail_header"),
        "",
        f"{card.title}",
        f"source: {card.source_type} #{card.source_id}",
        f"status: {card.status} ({card.status_label}) · tone={card.status_tone} · priority={card.priority}",
        "",
        translate(
            language_code,
            "admin_automation_cockpit_card_action_block",
            code=card.next_best_action_code,
            label=card.next_best_action_label,
            kind=card.next_best_action_kind,
            enabled=card.next_best_action_enabled,
        ),
        "",
        f"blocker: {card.blocker_summary or '—'}",
        f"warning: {card.warning_summary or '—'}",
        f"risk: {card.risk_summary or '—'}",
        f"owner: {card.owner_role or '—'}",
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
        lines.append(f"publish_status: {ctx.publish_status or '—'}")
        lines.append(f"preview_status: {ctx.preview_status or '—'}")
        lines.append(f"payload_status: {ctx.payload_status or '—'}")
        lines.append(f"template_family: {ctx.template_family or '—'}")
        lines.append(f"selected_template_id: {ctx.selected_template_id or '—'}")
        lines.append(f"tour_code: {ctx.tour_code or '—'}")
        lines.append(f"already_published: {ctx.already_published if ctx.already_published is not None else '—'}")
        lines.append(f"has_tour_bridge: {ctx.has_tour_bridge if ctx.has_tour_bridge is not None else '—'}")
        lines.append(
            f"has_catalog_visible_tour: {ctx.has_catalog_visible_tour if ctx.has_catalog_visible_tour is not None else '—'}"
        )
        lines.append(
            f"has_active_execution_link: {ctx.has_active_execution_link if ctx.has_active_execution_link is not None else '—'}"
        )
        lines.append("")
        note = (ctx.fact_lock_note or "").strip()
        if note:
            lines.append(note[:500])
    return "\n".join(lines)


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
            label = translate(
                language_code,
                "admin_automation_cockpit_open_card_btn",
                sid=c.source_id,
            )
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
