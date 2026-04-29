"""Format ``operator_workflow`` (Slice B read-model) for Telegram admin offer cards — compact plain text."""

from __future__ import annotations

import re
from typing import Callable

from app.schemas.supplier_admin import AdminSupplierOfferOperatorWorkflowRead

_WARNING_CODE_RE = re.compile(r"^\s*\[([^\]]+)\]")


def _compact_warning_line(raw: str, *, max_len: int = 48) -> str:
    """Prefer stable warning codes (``[code] message`` or plain codes); trim noise for mobile."""
    s = raw.strip()
    m = _WARNING_CODE_RE.match(s)
    if m:
        return m.group(1)
    one = s.split("\n", 1)[0].strip()
    if len(one) <= max_len:
        return one
    return one[: max_len - 1].rstrip() + "…"


def _truncate_blocking(raw: str, *, max_len: int = 52) -> str:
    s = raw.strip().replace("\n", " ")
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def _risk_label_key(danger_level: str) -> str:
    return {
        "safe_read": "admin_offer_operator_workflow_risk_safe_read",
        "safe_mutation": "admin_offer_operator_workflow_risk_safe_mutation",
        "conversion_enabling": "admin_offer_operator_workflow_risk_conversion_enabling",
        "public_dangerous": "admin_offer_operator_workflow_risk_public_dangerous",
    }.get(danger_level, "admin_offer_operator_workflow_risk_unknown")


def format_operator_workflow_for_telegram(
    ow: AdminSupplierOfferOperatorWorkflowRead,
    *,
    language_code: str | None,
    translate_fn: Callable[..., str],
    max_chars: int = 1400,
) -> str:
    """Compact operator hints from ``GET …/review-package`` — formatting only, no API calls.

    Caps: up to 3 blocking snippets and 3 warning codes (full review-package remains source of truth).
    """
    lines: list[str] = [translate_fn(language_code, "admin_offer_operator_workflow_header")]
    lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_state", state=ow.state))

    pa = None
    if ow.primary_next_action:
        pa = next((a for a in ow.actions if a.code == ow.primary_next_action), None)

    if pa is not None:
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_next", code=pa.code))
        risk_human = translate_fn(language_code, _risk_label_key(pa.danger_level))
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_risk", risk=risk_human))
        yes = translate_fn(language_code, "admin_offer_operator_workflow_yes")
        no = translate_fn(language_code, "admin_offer_operator_workflow_no")
        c_lab = yes if pa.requires_confirmation else no
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_confirm", confirm=c_lab))
        if pa.danger_level == "public_dangerous":
            lines.append(translate_fn(language_code, "admin_offer_operator_workflow_public_hint_short"))
    elif ow.primary_next_action:
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_line_next", code=ow.primary_next_action))
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
        for br in ow.blocking_reasons[:3]:
            lines.append(f"• {_truncate_blocking(br)}")

    if ow.warnings:
        lines.append(
            translate_fn(
                language_code,
                "admin_offer_operator_workflow_warnings_intro",
                count=str(len(ow.warnings)),
            ),
        )
        for w in ow.warnings[:3]:
            lines.append(f"• {_compact_warning_line(w)}")

    footer = translate_fn(language_code, "admin_offer_operator_workflow_footer_compact")
    body = "\n".join(lines)
    cap = max_chars - len(footer) - 2
    if len(body) > cap:
        body = body[: max(cap - 16, 0)].rstrip() + "\n…"
    return body + "\n\n" + footer


__all__ = ["format_operator_workflow_for_telegram"]
