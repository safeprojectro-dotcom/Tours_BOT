"""Format ``operator_workflow`` (Slice B read-model) for Telegram admin offer cards — plain text, read-only."""

from __future__ import annotations

from typing import Callable

from app.schemas.supplier_admin import AdminSupplierOfferOperatorWorkflowRead


def format_operator_workflow_for_telegram(
    ow: AdminSupplierOfferOperatorWorkflowRead,
    *,
    language_code: str | None,
    translate_fn: Callable[..., str],
    max_chars: int = 2200,
) -> str:
    """Human-readable operator hints from ``GET …/review-package`` — formatting only, no API calls.

    Caps match HANDOFF: up to 3 blocking lines and 3 warning lines.
    """
    lines: list[str] = [
        translate_fn(language_code, "admin_offer_operator_workflow_header"),
        translate_fn(language_code, "admin_offer_operator_workflow_state", state=ow.state),
    ]
    pa = None
    if ow.primary_next_action:
        pa = next((a for a in ow.actions if a.code == ow.primary_next_action), None)
    if pa is not None:
        lines.append(
            translate_fn(
                language_code,
                "admin_offer_operator_workflow_next_primary",
                code=pa.code,
                label=pa.label,
                danger=pa.danger_level,
                confirm=("yes" if pa.requires_confirmation else "no"),
            ),
        )
        lines.append(
            translate_fn(
                language_code,
                "admin_offer_operator_workflow_endpoint_hint",
                method=pa.method,
                endpoint=pa.endpoint,
            ),
        )
        if pa.danger_level == "public_dangerous":
            lines.append(translate_fn(language_code, "admin_offer_operator_workflow_public_danger_note"))
    elif ow.primary_next_action:
        lines.append(
            translate_fn(language_code, "admin_offer_operator_workflow_next_code", code=ow.primary_next_action),
        )
    else:
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_next_none"))

    if ow.blocking_reasons:
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_blocking_title"))
        for br in ow.blocking_reasons[:3]:
            lines.append(f"• {br}")

    if ow.warnings:
        lines.append(translate_fn(language_code, "admin_offer_operator_workflow_warnings_title"))
        for w in ow.warnings[:3]:
            lines.append(f"• {w}")

    footer = translate_fn(language_code, "admin_offer_operator_workflow_footer")
    body = "\n".join(lines)
    cap = max_chars - len(footer) - 2
    if len(body) > cap:
        body = body[: max(cap - 16, 0)] + "\n…"
    return body + "\n\n" + footer


__all__ = ["format_operator_workflow_for_telegram"]
