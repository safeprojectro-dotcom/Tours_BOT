# CURSOR_PROMPT_DEMO1_PHYSICAL_TELEGRAM_DEMO_SMOKE_PLAYBOOK

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a new architecture block.

## Cursor mode

Agent

## Block

DEMO-1 — Physical Telegram Demo Smoke / Playbook

## Execution mode

Docs-only / manual smoke playbook.

## Goal

Create a clear manual demo/smoke playbook for the already implemented physical Telegram demo chain.

This step must not change runtime code.

The purpose is to help the operator/admin physically demonstrate the system:

1. supplier offer / tour appears in channel;
2. customer can reserve/order;
3. supplier notification outbox rows are created;
4. supplier receives Telegram notifications via manual outbox delivery;
5. operational sales push preview can be generated;
6. operational sales push can be published to Telegram channel.

This is not a product roadmap block.
This is not M1.
This is not O1.
This is not S1E.
This is only a demo readiness/playbook document.

---

## Source docs/files to inspect

Inspect:

1. `docs/CHAT_HANDOFF.md`
2. `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
3. `P0_OPERATIONAL_AUTOMATION_ROADMAP_CHECKPOINT.txt`
4. Existing S1C/S1D prompt and handoff docs if present:
   - `docs/HANDOFF_S1C2_SUPPLIER_NOTIFICATION_TELEGRAM_DELIVERY_FROM_OUTBOX.md`
   - `docs/HANDOFF_S1C3_WIRE_SUPPLIER_NOTIFICATION_AFTER_CHANNEL_PUBLISH.md`
   - `docs/HANDOFF_S1C4_WIRE_SUPPLIER_NOTIFICATION_AFTER_CUSTOMER_ORDER.md`
   - `docs/HANDOFF_S1D1_OPERATIONAL_SALES_PUSH_ELIGIBILITY_AND_PREVIEW.md`
   - `docs/HANDOFF_S1D2_ADMIN_GATED_OPERATIONAL_SALES_PUSH_CHANNEL_PUBLISH.md`

Inspect relevant routes/services if needed only to document exact paths:

- supplier notification outbox routes
- operational sales push preview/publish routes
- supplier offer publish route
- Mini App reservation/order routes
- admin auth pattern

---

## Required new document

Create:

```text
docs/DEMO1_PHYSICAL_TELEGRAM_DEMO_SMOKE_PLAYBOOK.md