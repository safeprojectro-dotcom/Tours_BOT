# HANDOFF_A6E — Mobile admin compact summary & action clarity

**Scope:** Telegram admin read-only formatting / i18n (A6E). No DB, no services, no routing.

## Changes

1. **Queue list (cockpit lanes)** — Each card is up to **4 lines**: title, `source · status`, **`Reason` / `Motiv`**, **`Step` / `Pas`**. Catalog readiness is folded into the reason line when there is no clearer blocker (no extra 🧭 line). Dirty titles containing obvious internal tokens are replaced with a short placeholder.
2. **Card detail** — Opens with **`In short` / `Pe scurt`**: primary issue, preferred next step (catalog snap next step when present), one-line **internal** note (“nothing sent automatically”). Removed duplicate main-blocker / suggested-step blocks. **Commercial** block + fact lock only when there are non-empty commercial rows.
3. **Commercial context** — Drops “booking link: No” style rows; keeps positive flags (e.g. active booking link) and meaningful publish/preview rows.
4. **A6A detail section** — Compact: status + main blocker on one line, at most one warning line, then compact next step.
5. **Conversion panel (C2B11A)** — Generic internal details are **not** repeated under every row; **at most one** `admin_conversion_panel_verification_footer` line when any layer had a generic detail.
6. **Dates** — Outbox list/detail use `format_admin_datetime_compact` → `DD.MM.YYYY, HH:MM`.
7. **Buttons (RO)** — `admin_a6b_btn_continue_in_operator_workflow` → **“Flux ofertă”**; showcase preview button → **“Previzualizare”**.

## Safety

- No publishing, supplier notifications, tour/link/catalog mutations, Layer A, B11, or business-rule changes — text/formatting only.

## Tests

- `tests/unit/test_automation_cockpit_telegram.py` (added `format_admin_datetime_compact` test; queue/detail assertions updated)
- `tests/unit/test_supplier_offer_conversion_status_panel.py` (generic footer once)
- `tests/unit/test_operator_workflow_c2b3_keyboard.py` (RO preview label)
- Plus existing workflow/conversion tests

Suggested run:  
`python -m compileall app tests`  
`python -m pytest tests/unit/test_automation_cockpit_telegram.py tests/unit/test_operator_workflow_telegram_format.py tests/unit/test_supplier_offer_conversion_status_panel.py tests/unit/test_operator_workflow_c2b3_keyboard.py -q`

## Known rough edges

- Queue **Reason** text can still be English if the upstream blocker string is English (data issue, not formatter).
- Title sanitizer uses a fixed denylist; odd supplier strings may still slip through if they do not match tokens.
