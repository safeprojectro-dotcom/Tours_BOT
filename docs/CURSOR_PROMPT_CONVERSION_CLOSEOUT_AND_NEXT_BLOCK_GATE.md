# CURSOR_PROMPT_CONVERSION_CLOSEOUT_AND_NEXT_BLOCK_GATE

You are working on Tours_BOT.

Run a larger closeout/design gate block after the Telegram conversion workflow and media foundation checkpoint.

This is a docs/design/readiness block, not an application-code block.

## Purpose

Close the recent work cleanly and stop the endless micro-step chain.

This block must consolidate:

1. Production/OPS smoke readiness.
2. B10.6 Bot-as-router design gate.
3. Admin/OPS visibility polish design.
4. Media pipeline pause confirmation.
5. Recommended next implementation block.

## Current checkpoint

Recently completed:

### Telegram conversion workflow

- C2B8B — Telegram `Publică / Publish`
  - gated by `operator_workflow.actions.publish_showcase_channel.enabled`
  - propose/confirm re-read review-package
  - legacy one-step publish retired

- C2B10T-A — Telegram `Link tour / Leagă tur`
  - gated by `operator_workflow.actions.create_tour_bridge.enabled`
  - creates/links Tour bridge only

- C2B10T-B — Telegram `List for sale / În catalog`
  - gated by `operator_workflow.actions.activate_tour_for_catalog.enabled`
  - activates linked Tour for catalog only

- C2B10T-C — Telegram `Booking link / Link rezervări`
  - gated by `operator_workflow.actions.create_execution_link.enabled`
  - creates/replaces active execution link only

- C2B10T-D — OPS smoke/runbook validation
  - docs/readiness
  - current Telegram keyboard order:
    `Link tour → List for sale → Publish → Booking link`

### Media foundation

- B7.4A — readiness audit
- B7.4B — ingestion contract/design
- B7.4C — conservative implementation foundation
- B7.4D — `publish_safe` vNext metadata helpers

Media pipeline is intentionally paused. Do not continue B7.4D2/B7.4C2/B7.4E/B7.5/B7.6 in this block.

## Core architecture rules

Preserve:

- published != bookable
- linked != catalog-visible
- catalog-visible != execution-linked
- execution-linked != paid/confirmed booking
- Layer A remains booking/payment/order truth
- Mini App execution truth remains strict/current
- UI/Bot must not invent readiness logic
- Telegram workflow buttons rely on `operator_workflow.actions.*.enabled`
- dangerous actions require propose/confirm and fresh review-package re-read
- no hidden Tour creation
- no hidden publish
- no hidden execution link
- no hidden media ingestion
- no change to publish readiness
- no change to booking/payment/order behavior

## Docs to inspect

Inspect:

- `docs/CHAT_HANDOFF.md`
- `docs/TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`
- `docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`
- `docs/ADMIN_OPERATOR_WORKFLOW.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`
- `docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`
- `docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- existing B10.6 / B11 / bot routing docs if present

If files are missing, report clearly and continue.

## Code to inspect read-only

Read-only inspection only:

- `app/services/supplier_offer_operator_workflow.py`
- `app/bot/handlers/admin_moderation.py`
- `app/services/supplier_offer_bot_start_routing.py`
- `app/services/supplier_offer_deep_link.py`
- `app/bot/handlers/private_entry.py`
- Mini App supplier offer landing/read services if present
- review-package/conversion_closure services
- tests around:
  - B11 supoffer routing
  - supplier offer catalog conversion closure
  - Telegram admin moderation
  - operator workflow keyboard

Do not edit code.

## Deliverable 1 — OPS smoke readiness finalization

Update or create a concise ops smoke section/doc.

Preferred file:

`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`

It must include:

### Safe read-only checks

PowerShell examples:

```powershell
$r = Invoke-RestMethod -Uri "$BASE/admin/supplier-offers/<OFFER_ID>/review-package" -Headers $Headers -Method GET
$r.operator_workflow.actions | Format-Table code, enabled, danger_level, requires_confirmation, disabled_reason -AutoSize
$r.conversion_closure | Format-List
$r.linked_tour_catalog | Format-List