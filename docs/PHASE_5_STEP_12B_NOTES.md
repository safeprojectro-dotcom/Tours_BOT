# Phase 5 / Step 12B — Reusable / editable Telegram home & catalog messages

## Scope

**Allowed:** `app/bot/transient_messages.py`, `private_entry.py`, `messages.py` / `keyboards.py` only if needed (no changes required for this slice), docs, narrow unit tests.

**Out of scope:** booking/payment logic, Mini App, schema, webhooks, admin, waitlist.

## Policy

- In-memory registry keys **`HOME_MESSAGE`** and **`CATALOG_MESSAGE`** hold the last bot message ids for the welcome row and the short tour list (same two-message layout as before).
- **Commands `/start`** (catalog path) and **`/tours`**: `_send_catalog_overview(..., prefer_edit=True)` calls **`send_or_edit_home_catalog_pair`**, which:
  1. If both ids are known: **`edit_message_text`** (and reply markup) on both; on success, clears tracked **language** + **filter** prompts only; ids stay the same.
  2. If edit raises **any** exception (message gone, too old, wrong type, etc.): **delete** the two tracked ids best-effort, drop them from the store, then **`answer` ×2** and **`register_catalog_bundle`** (same as Step 12A delete+register path).
- **Browse/filter callbacks** and **filtered catalog** still use **`prefer_edit=False`**: always send two new messages and register (no edit), so Step 12A stacking behavior remains for those flows.

## Files

- `app/bot/transient_messages.py` — `send_or_edit_home_catalog_pair`, `_clear_language_and_filter_prompts`, `HOME_MESSAGE` / `CATALOG_MESSAGE` store keys (replaces former `catalog_welcome` / `catalog_list` names).
- `app/bot/handlers/private_entry.py` — `_send_catalog_overview(..., prefer_edit)`; `True` only for `/start` and `/tours`.

## Manual smoke (Step 12B)

1. `/start` several times (with language set) — same two bot messages update in place when Telegram allows edit.
2. `/tours` several times — same behavior.
3. Trigger payment/reservation/help — anchor messages unchanged.
4. `/language` and filter flows — Step 12A cleanup still works; browse from buttons may still add new pair (by design).

## Verification

- `python -m compileall app/bot/transient_messages.py app/bot/handlers/private_entry.py`
- `python -m unittest tests.unit.test_transient_messages -v`
