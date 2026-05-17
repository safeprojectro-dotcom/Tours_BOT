"""Format ``operator_workflow`` (Slice B read-model) for Telegram admin offer cards — compact plain text."""

from __future__ import annotations

import re
from typing import Callable

from app.bot.automation_cockpit_telegram import humanize_admin_text
from app.bot.messages import TRANSLATIONS
from app.schemas.supplier_admin import AdminSupplierOfferOperatorWorkflowRead

_WARNING_CODE_RE = re.compile(r"^\s*\[([^\]]+)\]")


def _compact_warning_line(raw: str, language_code: str | None, *, max_len: int = 48) -> str:
    """Prefer stable warning codes (``[code] message`` or plain codes); trim noise for mobile."""
    s = raw.strip()
    m = _WARNING_CODE_RE.match(s)
    core = m.group(1) if m else s.split("\n", 1)[0].strip()
    h = humanize_admin_text(language_code, core)
    if len(h) <= max_len:
        return h
    return h[: max_len - 1].rstrip() + "…"


def _truncate_blocking(raw: str, language_code: str | None, *, max_len: int = 52) -> str:
    h = humanize_admin_text(language_code, raw.strip().replace("\n", " "))
    if len(h) <= max_len:
        return h
    return h[: max_len - 1].rstrip() + "…"


def _risk_label_key(danger_level: str) -> str:
    return {
        "safe_read": "admin_offer_operator_workflow_risk_safe_read",
        "safe_mutation": "admin_offer_operator_workflow_risk_safe_mutation",
        "conversion_enabling": "admin_offer_operator_workflow_risk_conversion_enabling",
        "public_dangerous": "admin_offer_operator_workflow_risk_public_dangerous",
    }.get(danger_level, "admin_offer_operator_workflow_risk_unknown")


def _humanize_workflow_state(
    language_code: str | None,
    state: str,
    translate_fn: Callable[..., str],
) -> str:
    key = f"admin_offer_ow_state_{state}"
    if key not in TRANSLATIONS["en"]:
        return humanize_admin_text(language_code, state.replace("_", " "))
    return translate_fn(language_code, key)


def _humanize_action_code(
    language_code: str | None,
    code: str,
    translate_fn: Callable[..., str],
) -> str:
    key = f"admin_offer_ow_action_{code}"
    if key not in TRANSLATIONS["en"]:
        return humanize_admin_text(language_code, code.replace("_", " "))
    return translate_fn(language_code, key)


def format_operator_workflow_for_telegram(
    ow: AdminSupplierOfferOperatorWorkflowRead,
    *,
    language_code: str | None,
    translate_fn: Callable[..., str],
    max_chars: int = 1400,
) -> str:
    """Compact operator hints from review-package — formatting only, no API calls.

    Caps: up to 3 blocking snippets and 3 warning codes (full review-package remains source of truth).
    """
    state_h = _humanize_workflow_state(language_code, ow.state, translate_fn)
    lines: list[str] = [translate_fn(language_code, "admin_offer_operator_workflow_header")]
    lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_state", state=state_h))

    pa = None
    if ow.primary_next_action:
        pa = next((a for a in ow.actions if a.code == ow.primary_next_action), None)

    if pa is not None:
        step_h = _humanize_action_code(language_code, pa.code, translate_fn)
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_next", step=step_h))
        risk_human = translate_fn(language_code, _risk_label_key(pa.danger_level))
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_risk", risk=risk_human))
        yes = translate_fn(language_code, "admin_offer_operator_workflow_yes")
        no = translate_fn(language_code, "admin_offer_operator_workflow_no")
        c_lab = yes if pa.requires_confirmation else no
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_confirm", confirm=c_lab))
        if pa.danger_level == "public_dangerous":
            lines.append(translate_fn(language_code, "admin_offer_operator_workflow_public_hint_short"))
    elif ow.primary_next_action:
        step_h = _humanize_action_code(language_code, ow.primary_next_action, translate_fn)
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_next", step=step_h))
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_next_detail_missing"))
    else:
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_next_none"))

    if ow.blocking_reasons:
        lines.append(
            translate_fn(
                language_code,
                "admin_offer_operator_workflow_blocking_intro",
                count=str(len(ow.blocking_reasons)),
            ),
        )
        seen_block: set[str] = set()
        for br in ow.blocking_reasons[:3]:
            bline = _truncate_blocking(br, language_code)
            if bline in seen_block:
                continue
            seen_block.add(bline)
            lines.append(f"• {bline}")

    if ow.warnings:
        lines.append(
            translate_fn(
                language_code,
                "admin_offer_operator_workflow_warnings_intro",
                count=str(len(ow.warnings)),
            ),
        )
        seen_warn: set[str] = set()
        for w in ow.warnings[:3]:
            wline = _compact_warning_line(w, language_code)
            if wline in seen_warn:
                continue
            seen_warn.add(wline)
            lines.append(f"• {wline}")

    footer = translate_fn(language_code, "admin_offer_operator_workflow_footer_compact")
    body = "\n".join(lines)
    cap = max_chars - len(footer) - 2
    if len(body) > cap:
        body = body[: max(cap - 16, 0)].rstrip() + "\n…"
    return body + "\n\n" + footer


__all__ = ["format_operator_workflow_for_telegram"]
