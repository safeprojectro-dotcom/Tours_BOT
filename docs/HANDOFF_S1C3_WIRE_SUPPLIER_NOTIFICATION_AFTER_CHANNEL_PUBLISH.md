# HANDOFF_S1C3_WIRE_SUPPLIER_NOTIFICATION_AFTER_CHANNEL_PUBLISH

## Project

Tours_BOT

## Block

S1C-3 — Wire Supplier Notification After Channel Publish using Outbox Only

## Purpose

After successful supplier offer channel publish, enqueue supplier notification into `supplier_notification_outbox`.

## Mode

Narrow-step mode.

Reason:
- publish flow is a public side effect;
- supplier notification is an external side effect;
- this step must only queue notification, not send it.

## Included

- find central supplier offer channel publish success path;
- enqueue `supplier_offer_published` notification after successful publish;
- use S1C-1 outbox service;
- preserve idempotency;
- do not fail publish on missing supplier Telegram contact;
- add focused tests;
- docs checkpoint.

## Excluded

- no direct supplier Telegram send;
- no S1C-2 delivery call from publish;
- no scheduler/worker;
- no customer order hook;
- no extra channel publish;
- no passenger manifest;
- no customer personal data;
- no Layer A mutation;
- no payment/reconciliation changes;
- no seat inventory mutation;
- no B11 routing change;
- no QR;
- no marketing broadcast;
- no outbox bypass.

## Expected future blocks

- S1C-4 — Wire supplier notification after customer reservation/order using outbox only.
- S1D — Admin-gated last-seats operational publish.

## Verification expected

Run:

```bash
python -m compileall app tests