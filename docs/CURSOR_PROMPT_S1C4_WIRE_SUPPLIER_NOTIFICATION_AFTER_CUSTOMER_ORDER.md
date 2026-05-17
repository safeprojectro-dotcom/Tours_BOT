# CURSOR_PROMPT_S1C4_WIRE_SUPPLIER_NOTIFICATION_AFTER_CUSTOMER_ORDER

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a redesign.

## Cursor mode

Agent

## Block name

S1C-4 — Wire Supplier Notification After Customer Reservation/Order using Outbox Only

## Execution mode

Narrow-step mode.

Reason:
- This block touches customer reservation/order creation flow.
- Customer reservation/order creation is Layer A sensitive.
- Supplier notification is an external side effect.
- This block must NOT send supplier Telegram messages directly.
- This block may only enqueue a supplier notification outbox record after a successful Layer A reservation/order creation.
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

S1C-3 completed:
- after successful supplier offer showcase/channel publish, the system enqueues `supplier_offer_published` outbox row.
- no direct supplier send.

S1C-4 must now connect successful customer reservation/order creation to the S1C-1 outbox enqueue service.

---

## Goal

When a customer successfully creates a reservation/order for a supplier-linked tour, enqueue a `supplier_order_created` notification into `supplier_notification_outbox`.

The flow must be:

```text
customer creates reservation/order through existing Layer A flow
→ Layer A order creation succeeds
→ supplier_notification_outbox row is created/replayed
→ supplier message is NOT sent automatically
→ admin/manual delivery endpoint can send it later