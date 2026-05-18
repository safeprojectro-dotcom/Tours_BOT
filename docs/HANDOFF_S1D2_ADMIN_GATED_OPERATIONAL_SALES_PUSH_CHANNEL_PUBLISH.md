# HANDOFF_S1D2_ADMIN_GATED_OPERATIONAL_SALES_PUSH_CHANNEL_PUBLISH

## Project

Tours_BOT

## Block

S1D-2 — Admin-Gated Operational Sales Push Channel Publish

## Purpose

Publish operational sales push messages to Telegram channel only after explicit admin action and only from eligible S1D-1 preview.

## Mode

Narrow-step mode.

Reason:
- real Telegram channel publish is a public external side effect;
- urgency/scarcity claims must be system-confirmed;
- no scheduler or automatic publish in this block.

## Included

- re-run S1D-1 preview at publish time;
- publish only if eligible;
- send only system-generated preview text;
- add protected admin POST endpoint if safe;
- fake sender tests;
- docs checkpoint.

## Excluded

- no scheduler/worker;
- no automatic publish by date;
- no automatic publish by seats threshold;
- no supplier notification send;
- no customer personal data;
- no passenger manifest;
- no Layer A mutation;
- no payment/reconciliation changes;
- no seat inventory mutation;
- no B11 routing changes;
- no QR;
- no marketing broadcast;
- no arbitrary admin text publish.

## Expected demo capability

After S1D-2:

```text
Admin checks operational sales push preview
→ Admin explicitly publishes
→ Telegram channel receives operational sales push post
→ CTA directs customer to Mini App/tour path if available