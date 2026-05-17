# HANDOFF_S1C1_SUPPLIER_NOTIFICATION_OUTBOX_FOUNDATION

## Project

Tours_BOT

## Block

S1C-1 — Supplier Notification Outbox & Payload Foundation

## Purpose

Create a governed supplier notification foundation before actual Telegram sends.

This block prepares notification payloads and optionally persists outbox records for future delivery.

## Mode

Narrow-step mode.

Reason:
- supplier notifications are external visible side effects;
- outbox/idempotency/audit foundation must exist before send;
- this block must not send Telegram messages.

## Included

- inspect existing notification/outbox patterns;
- define supplier notification event types;
- prepare safe payloads for:
  - supplier_offer_published
  - supplier_order_created
- use S1B supplier contact resolver;
- add outbox/pending/skipped foundation if safe;
- add deterministic idempotency;
- add focused tests;
- update handoff and open questions.

## Excluded

- no actual Telegram send
- no Telegram channel publish
- no scheduler/workers
- no passenger manifest
- no customer personal data
- no payment/reconciliation changes
- no order/reservation/payment mutation
- no seat inventory mutation
- no B11 routing change
- no marketing broadcast
- no QR
- no fake availability/order/payment status
- no hardcoded chat ids

## Message data allowed

Allowed:
- supplier id
- offer id
- tour id
- order id/reference
- tour/offer title
- departure date
- seats count
- payment status summary

Forbidden:
- customer name
- phone
- Telegram ID
- email
- document/passenger list
- payment sensitive data

## Expected future blocks

- S1C-2 — Supplier Notification Telegram Delivery from Outbox
- S1C-3 — Wire notification after channel publish
- S1C-4 — Wire notification after customer reservation/order

## Verification expected

Run:

```bash
python -m compileall app tests