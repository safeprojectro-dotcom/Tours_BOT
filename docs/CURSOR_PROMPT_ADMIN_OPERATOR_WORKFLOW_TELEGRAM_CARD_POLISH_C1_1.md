# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_TELEGRAM_CARD_POLISH_C1_1

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN OPERATOR WORKFLOW — Slice C1.1

Telegram operator workflow card polish / compact mode.

---

## Context

Slice C1 is implemented and manually verified in production Telegram.

Telegram admin offer card now displays read-only operator_workflow from review-package:

- state
- primary_next_action
- danger_level
- confirmation flag
- endpoint hint
- warnings
- read-only footer

Manual check passed, but the block is too long and too technical for Telegram.

Observed issues:

- long endpoint takes too much space;
- warnings are verbose English technical messages;
- danger/confirm line is too raw;
- footer is long;
- operator card becomes hard to scan on mobile.

This slice should improve readability only.

---

## Strict boundaries

Do not change booking/payment/order/reservation.
Do not change Mini App UI.
Do not change Telegram showcase template.
Do not change publish behavior.
Do not change Tour bridge/catalog activation behavior.
Do not add migrations.
Do not call external AI.
Do not add Telegram action buttons.
Do not add web UI.
Do not add batch/macro endpoints.
Do not execute operator_workflow actions from Telegram.
Do not auto-publish.
Do not auto-create Tour.
Do not auto-activate catalog.
Do not auto-create execution link.

This is display-only polish.

---

## Goal

Make the operator_workflow block in Telegram admin card compact and operator-friendly.

Keep the full review-package endpoint as source of truth.

---

## Current files likely involved

Inspect:

- app/bot/supplier_offer_operator_workflow_telegram.py
- app/bot/handlers/admin_moderation.py
- app/bot/messages.py
- tests/unit/test_operator_workflow_telegram_format.py
- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

---

## Required behavior

### 1. Compact block format

Change Telegram block from verbose format to compact format.

Suggested format:

```text
— Flux operator —
Stare: awaiting_moderation_approval
Următor: approve_offer_moderation
Risc: safe_mutation
Confirmare: nu
Avertismente: 3
• orphan_promo_code
• discount_deadline_without_value
• description_thin

Read-only: acțiunile se execută separat.