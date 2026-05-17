# CURSOR_PROMPT_A6B_CATALOG_CONVERSION_GUIDED_ACTIONS

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

## Block

A6B — Catalog / Conversion Guided Actions

## Mode

Functional block mode with guarded boundaries.

Reason:
A6A already added a read-only catalog/conversion readiness snapshot into Admin Automation Cockpit and Telegram surfaces.
A6B should make that snapshot operationally useful by adding safe next-action buttons/hints, but must not execute dangerous conversion mutations automatically.

This is a larger functional block because it is mostly Telegram/admin UX wiring and action routing around existing guarded flows.
However, any actual mutation must remain behind existing explicit confirm/propose flows.

## Context

Recent completed checkpoint:

- commit: `6a87691`
- A6A added catalog conversion readiness snapshot
- files touched included:
  - `app/bot/automation_cockpit_telegram.py`
  - `app/bot/messages.py`
  - `app/schemas/admin_automation_cockpit.py`
  - `app/services/admin_automation_cockpit_service.py`
  - `app/services/supplier_offer_catalog_conversion_readiness_service.py`
  - tests for supplier offer readiness, admin cockpit, Telegram formatter

Current visible behavior:
- cockpit detail shows `🧭 Catalog / conversie`
- it explains status/blocker/warnings/next step
- but admin still needs obvious guided buttons to act on the blocker

## Goal

Add safe guided action buttons for `Catalog / conversie` readiness states in the Telegram Admin Automation Cockpit.

The admin should see the readiness status and then get context-aware action buttons that guide them to the existing safe flow.

Examples:
- Missing offer-tour bridge → button to existing guarded tour bridge/propose flow or offer detail where the guarded bridge button exists
- Tour exists but not catalog-active → button/hint to existing guarded catalog preparation/admin detail flow
- Missing execution link → button/hint to existing guarded conversion/execution-link flow if available, otherwise safe detail route/human-readable instruction
- Ready → no dangerous action button; show ready state and safe open detail/catalog/Mini App link if already supported

## Hard safety boundaries

Do NOT:
- create or mutate `Tour` directly from A6B
- activate catalog directly from A6B
- create execution links directly from A6B
- publish Telegram channel posts
- notify suppliers
- mutate orders/reservations/payments
- change Layer A booking/payment/reservation logic
- change PaymentEntryService or PaymentReconciliationService
- change B11 deep-link routing
- add migrations
- add new public side effects
- bypass existing readiness/propose/confirm gates
- expose raw backend enum tokens in Telegram text

A6B may:
- add Telegram inline buttons
- add callback routing to existing safe detail/propose flows
- add message formatting helpers
- add translation keys
- add tests
- add small schema/read fields only if needed for safe button decisions

## Required architecture rules

- service layer owns business/readiness decisions
- Telegram formatter must not duplicate complex readiness policy
- repositories remain persistence-only
- UI/bot layer only renders the action plan returned by service or deterministic formatter
- all user-facing text must use `translate()` keys
- Romanian and English copy must be provided
- no raw tokens like `missing_execution_link`, `prepare_chain`, `cta_safety`, `admin_a6a_` may leak to Telegram

## Expected implementation approach

1. Inspect current A6A implementation:
   - `app/services/supplier_offer_catalog_conversion_readiness_service.py`
   - `app/services/admin_automation_cockpit_service.py`
   - `app/bot/automation_cockpit_telegram.py`
   - `app/bot/messages.py`
   - related tests

2. Define a small action model if needed, for example:
   - `CatalogConversionGuidedActionRead`
   - action code / label key / callback target / enabled state / safety note
   But keep it minimal.

3. Add context-aware guided actions to cockpit card detail rendering:
   - missing bridge → safe button to existing offer detail / tour bridge guarded workflow if callback exists
   - missing catalog activation → safe button to existing offer/tour/admin detail or preparation route if callback exists
   - missing execution link → safe button or clear instruction to existing guarded flow
   - ready → safe open/view buttons only

4. Reuse existing callback prefixes and guarded flows where possible.
   Do not invent a new mutation callback if a guarded one already exists.

5. If no existing guarded callback exists for a blocker:
   - show a disabled/no-op style instruction as text
   - or route to safe detail screen
   - do not create a shortcut mutation.

6. Update Telegram list/detail tests:
   - buttons appear for missing bridge case
   - buttons do not appear for unsafe direct mutation
   - ready state does not show mutation buttons
   - Romanian copy is human-readable
   - no raw backend tokens leak

7. Keep docs minimal.
   Only update docs if necessary:
   - `docs/CHAT_HANDOFF.md`
   - `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
   Do not create broad new docs unless the implementation introduces a real new checkpoint.

## Expected files

Likely files:
- `app/bot/automation_cockpit_telegram.py`
- `app/bot/messages.py`
- `app/schemas/admin_automation_cockpit.py` only if needed
- `app/services/admin_automation_cockpit_service.py` only if needed
- `app/services/supplier_offer_catalog_conversion_readiness_service.py` only if needed
- `tests/unit/test_automation_cockpit_telegram.py`
- `tests/unit/test_admin_automation_cockpit.py`
- possibly `tests/unit/test_supplier_offer_catalog_conversion_readiness_service.py`

Avoid touching:
- migrations
- payment services
- reservation/order services
- public publishing services
- B11 deep-link routing

## Verification

Run:

```bash
python -m compileall app tests
pytest tests/unit/test_supplier_offer_catalog_conversion_readiness_service.py tests/unit/test_admin_automation_cockpit.py tests/unit/test_automation_cockpit_telegram.py -q