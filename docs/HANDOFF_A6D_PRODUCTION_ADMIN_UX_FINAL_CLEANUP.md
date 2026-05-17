# HANDOFF_A6D — Production admin UX final cleanup

**Block:** A6D — catalog/conversion Telegram admin flow, readability only (no Layer A / B11 / mutations / jobs).

## Done

- **Showcase template IDs:** `_showcase_template_label` + `admin_offer_showcase_tpl_unknown_fallback` — raw template tokens (e.g. `full_bus_private_group`) do not appear in compact B12B copy; known IDs map via `admin_offer_showcase_tpl_*` strings (EN/RO).
- **B12B compact block:** Header/lines aligned with “wording style” / suggested / preview / selection (RO strings added); removed legacy single-line inference key from RO.
- **Preview lifecycle:** `admin_offer_showcase_preview_lifecycle` — EN “Offer status”, RO “Stare ofertă” (no “Lifecycle:” label).
- **Booking link wording:** User-facing EN/RO strings prefer “booking link” / “link rezervări” over “execution link”; full RO coverage for `admin_offer_link_*` and link actions previously EN-fallback.
- **Buttons:** e.g. RO showcase preview → “Previzualizare showcase”.
- **Dedupe:** Conversion status panel omits repeated identical humanized detail lines; operator workflow dedupes identical blocking/warning bullets after humanization.
- **Tests:** `test_supplier_offer_conversion_status_panel.py` (detail dedupe), `test_operator_workflow_telegram_format.py` (warning/blocking dedupe), `test_operator_workflow_c2b3_keyboard.py` (RO labels).

## Verify manually (Telegram)

- `/admin_cockpit` → catalog/conversion card → supplier offer → guided flow: no raw template IDs, no repeated “Necesită verificare internă.” under every layer when details are the same, link button/screen reads as rezervări/booking not “exec”.

## Files touched

- `app/bot/messages.py`
- `app/bot/supplier_offer_conversion_status_panel_telegram.py`
- `app/bot/supplier_offer_operator_workflow_telegram.py`
- `tests/unit/test_supplier_offer_conversion_status_panel.py`
- `tests/unit/test_operator_workflow_telegram_format.py`
- `tests/unit/test_operator_workflow_c2b3_keyboard.py`
