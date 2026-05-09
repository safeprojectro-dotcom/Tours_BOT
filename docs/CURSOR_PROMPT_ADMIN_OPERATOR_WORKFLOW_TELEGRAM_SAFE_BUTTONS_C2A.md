# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_TELEGRAM_SAFE_BUTTONS_C2A

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

---

## Functional block

ADMIN OPERATOR WORKFLOW — Slice C2A

Telegram safe action buttons consuming operator_workflow.

---

## Context

Already implemented and deployed:

- Slice B: GET /admin/supplier-offers/{offer_id}/review-package includes read-only operator_workflow.
- Slice C1: Telegram admin offer card displays operator_workflow.
- Slice C1.1: Telegram operator workflow card was compacted.

Current Telegram card is display-only.

Now we start using operator_workflow.actions for buttons, but only low-risk/read-only actions.

---

## Strict boundaries

Do not change booking/payment/order/reservation.
Do not change Mini App UI.
Do not change Telegram showcase template.
Do not change publish behavior.
Do not change Tour bridge/catalog activation behavior.
Do not add migrations.
Do not call external AI.
Do not add web UI.
Do not add batch/macro endpoints.
Do not auto-publish.
Do not auto-create Tour.
Do not auto-activate catalog.
Do not auto-create execution link.

Do not add buttons for these actions in C2A:

- publish_showcase_channel
- activate_tour_for_catalog
- create_execution_link
- create_tour_bridge

These are explicitly postponed to later slices with confirmation design.

C2A may add only safe/read-only buttons and, if already existing, must not duplicate old approve/reject behavior.

---

## Goal

Add Telegram admin buttons that consume `operator_workflow.actions` only for safe/read-only actions.

Minimum target buttons:

1. Refresh operator workflow / review package.
2. Show compact workflow details again.
3. Optionally show showcase preview as read-only if existing service makes this safe and no Telegram send occurs.

Do not execute mutating POST-style actions from operator_workflow yet.

---

## Source files to inspect

Inspect:

- app/bot/handlers/admin_moderation.py
- app/bot/supplier_offer_operator_workflow_telegram.py
- app/bot/keyboards.py
- app/bot/messages.py
- app/services/supplier_offer_review_package_service.py
- app/services/supplier_offer_operator_workflow.py
- tests/unit/test_operator_workflow_telegram_format.py
- tests/unit/test_telegram_admin_moderation_y281.py
- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

If admin Telegram callback routing is elsewhere, find equivalent files.

---

## Implementation requirements

### 1. Safe buttons only

Add inline/reply buttons only for safe/read-only operator actions.

Allowed action codes in C2A:

```text
review_package_refresh
get_showcase_preview