# HANDOFF_S1C4_WIRE_SUPPLIER_NOTIFICATION_AFTER_CUSTOMER_ORDER

## Project

Tours_BOT

## Block

S1C-4 — Wire Supplier Notification After Customer Reservation/Order using Outbox Only

## Purpose

After successful customer reservation/order creation, enqueue supplier notification into `supplier_notification_outbox`.

## Mode

Narrow-step mode.

Reason:
- customer reservation/order creation is Layer A sensitive;
- supplier notification is an external side effect;
- this step must only queue notification, not send it.

## Included

- find central customer reservation/order success path;
- enqueue `supplier_order_created` notification after successful order creation;
- use S1C-1 outbox service;
- preserve idempotency;
- do not fail order creation on missing/ambiguous supplier contact;
- add focused tests;
- docs checkpoint.

## Excluded

- no direct supplier Telegram send;
- no S1C-2 delivery call from order flow;
- no scheduler/worker;
- no channel publish;
- no passenger manifest;
- no customer personal data;
- no payment confirmation;
- no payment/reconciliation changes;
- no seat inventory semantic changes;
- no B11 routing change;
- no QR;
- no marketing broadcast;
- no outbox bypass.

## Expected future/demo capability

After S1C-4:

```text
Customer creates order
→ supplier_order_created outbox row appears
→ admin/manual S1C-2 delivery can send supplier notification