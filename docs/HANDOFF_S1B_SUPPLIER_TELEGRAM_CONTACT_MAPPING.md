# HANDOFF_S1B_SUPPLIER_TELEGRAM_CONTACT_MAPPING

## Project

Tours_BOT

## Block

S1B — Supplier Telegram Contact Mapping

## Purpose

Implement the smallest safe resolver that maps supplier / supplier offer / tour / order context to a supplier Telegram contact for future notifications.

## Mode

Narrow-step mode.

Reason:
- this prepares supplier Telegram notifications;
- supplier sends are external visible side effects;
- permissions/privacy must be controlled;
- no actual send is allowed in this block.

## Included

- Inspect supplier/user/telegram fields and relationships.
- Reuse existing supplier Telegram identity if present.
- Resolve supplier offer → supplier contact if safe.
- Resolve tour/order → supplier contact only through existing safe execution link / bridge / supplier relationships.
- Add optional admin read endpoint only if safe.
- Add focused tests.
- Update handoff and open questions.

## Excluded

- no supplier notifications
- no Telegram channel publish
- no send buttons
- no scheduler/workers
- no passenger manifest
- no personal customer data
- no payment/reconciliation changes
- no order/reservation/payment mutation
- no seat inventory mutation
- no B11 routing change
- no marketing broadcast
- no QR
- no fake supplier mapping
- no hardcoded production chat ids

## Expected output

A resolver such as:

- `SupplierTelegramContactResolver`
- `SupplierTelegramContactResolution`

that can return:

- configured true/false;
- telegram_chat_id if safely available;
- source;
- warnings;
- missing_reason.

## Safety

Missing contact must not crash future flows.

Ambiguous mapping must return a warning/missing result rather than guessing.

No customer personal data may appear in the result.

## Expected files

Likely:

- `app/services/supplier_telegram_contact.py`
- `app/schemas/supplier_telegram_contact.py`
- maybe existing admin route if endpoint added
- focused tests
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

## Verification expected

Run:

```bash
python -m compileall app tests