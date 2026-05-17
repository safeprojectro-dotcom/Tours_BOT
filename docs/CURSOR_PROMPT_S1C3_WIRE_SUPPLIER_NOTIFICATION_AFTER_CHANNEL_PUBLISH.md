# CURSOR_PROMPT_S1C3_WIRE_SUPPLIER_NOTIFICATION_AFTER_CHANNEL_PUBLISH

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a redesign.

## Cursor mode

Agent

## Block name

S1C-3 — Wire Supplier Notification After Channel Publish using Outbox Only

## Execution mode

Narrow-step mode.

Reason:
- This block touches the Telegram channel publish flow.
- Telegram channel publish is an external public side effect.
- Supplier notifications are external side effects.
- This block must NOT send supplier Telegram messages directly.
- This block may only enqueue a supplier notification outbox record after a successful channel publish.
- Actual supplier Telegram delivery remains S1C-2 manual delivery from outbox.

---

## Context

S1A completed:
- read-only supplier/tour/departure passenger counts.

S1B completed:
- supplier Telegram contact resolver.
- uses `Supplier.primary_telegram_user_id`.
- missing/ambiguous contact fails safely.

S1C-1 completed:
- `supplier_notification_outbox` table/model/repo/service.
- payload foundation for:
  - `supplier_offer_published`
  - `supplier_order_created`
- idempotency and skipped/no-target support.
- no send.

S1C-2 completed:
- manual Telegram delivery from outbox.
- `POST /admin/supplier-notification-outbox/{outbox_id}/deliver`.
- only sends from outbox.
- no automatic publish/order hooks.
- no scheduler.

S1C-3 must now connect the existing successful channel publish flow to the S1C-1 outbox enqueue service.

---

## Goal

When a supplier offer is successfully published to the Telegram channel, enqueue a `supplier_offer_published` notification into `supplier_notification_outbox`.

The flow must be:

```text
admin publishes supplier offer to Telegram channel
→ publish succeeds
→ supplier_notification_outbox row is created/replayed
→ supplier message is NOT sent automatically
→ admin/manual delivery endpoint can send it later