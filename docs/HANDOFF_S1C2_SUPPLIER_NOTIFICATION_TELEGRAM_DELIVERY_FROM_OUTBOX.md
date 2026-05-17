# HANDOFF_S1C2_SUPPLIER_NOTIFICATION_TELEGRAM_DELIVERY_FROM_OUTBOX

## Project

Tours_BOT

## Block

S1C-2 — Supplier Notification Telegram Delivery from Outbox

## Purpose

Implement controlled Telegram delivery for supplier notification outbox records.

## Mode

Narrow-step mode.

Reason:
- actual Telegram send is an external visible side effect;
- must only deliver already-created outbox records;
- no automatic business hook yet.

## Included

- process `supplier_notification_outbox` pending records;
- send message_text to stored telegram_chat_id;
- mark delivered / failed;
- no duplicate sends for delivered/skipped records;
- focused tests with fake bot/sender;
- optional explicit admin delivery endpoint only if safe;
- docs checkpoint.

## Excluded

- no automatic notification after publish;
- no automatic notification after order;
- no scheduler/worker loop;
- no Telegram channel publish;
- no passenger manifest;
- no customer personal data;
- no Layer A mutation;
- no payment/reconciliation changes;
- no seat inventory mutation;
- no B11 routing changes;
- no QR;
- no marketing broadcast;
- no hardcoded chat ids;
- no direct send outside outbox.

## Safety

Delivery must use stored outbox payload/message only.

Do not rebuild message from customer/order personal data at delivery time.

Missing/failed delivery must be recorded safely.

## Expected future blocks

- S1C-3 — Wire supplier notification after channel publish using outbox.
- S1C-4 — Wire supplier notification after customer reservation/order using outbox.
- S1D — Admin-gated last-seats operational publish.

## Verification expected

Run:

```bash
python -m compileall app tests