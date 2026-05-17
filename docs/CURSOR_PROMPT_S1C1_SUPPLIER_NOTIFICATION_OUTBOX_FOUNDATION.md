# CURSOR_PROMPT_S1C1_SUPPLIER_NOTIFICATION_OUTBOX_FOUNDATION

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a redesign.

## Cursor mode

Agent

## Block name

S1C-1 — Supplier Notification Outbox & Payload Foundation

## Execution mode

Narrow-step mode.

Reason:
- S1C prepares supplier notifications.
- Supplier notification send is an external visible side effect.
- This step must create the governed foundation before any actual Telegram send.
- No Telegram message should be sent in this block.
- No automatic trigger should send anything in this block.

---

## Context

S1A is completed:
- read-only departure passenger counts per supplier / tour / departure;
- admin GET routes;
- no supplier notification send;
- no passenger manifest;
- no Layer A mutation.

S1B is completed:
- supplier Telegram contact mapping / resolver;
- uses `Supplier.primary_telegram_user_id`;
- admin GET contact resolution routes;
- missing / ambiguous relationships fail safely;
- no supplier notification send.

S1C-1 must prepare safe supplier notification payload/outbox foundation for future actual sends.

Future S1C steps:
- S1C-2 — Supplier notification after channel publish
- S1C-3 — Supplier notification after customer reservation/order
- S1C-4 — Actual Telegram supplier outbox processing / send, if not included earlier and only after explicit approval

---

## Source documents to inspect first

Inspect if present:

1. `docs/CHAT_HANDOFF.md`
2. `docs/OPERATIONAL_AUTOMATION_ROADMAP.md`
3. `P0_OPERATIONAL_AUTOMATION_ROADMAP_CHECKPOINT.txt`
4. `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
5. `docs/IMPLEMENTATION_PLAN.md`
6. `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
7. `docs/TECH_SPEC_TOURS_BOT.md`
8. `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
9. `BUSINESS-план-v2.txt`

Also inspect existing notification/outbox patterns:
- notification outbox models/services
- Telegram delivery services
- supplier execution attempt Telegram idempotency, if present
- payment/order notification services
- S1A files
- S1B files

If `docs/OPERATIONAL_AUTOMATION_ROADMAP.md` is missing, do not recreate it. Mention it in the report and use `P0_OPERATIONAL_AUTOMATION_ROADMAP_CHECKPOINT.txt` as policy source.

---

## Goal

Create a safe supplier notification foundation that can prepare and persist supplier notification intents for future Telegram delivery.

This block must NOT send supplier Telegram messages yet.

It should support two future event types:

1. `supplier_offer_published`
   - supplier should later be notified that their offer/post was published.

2. `supplier_order_created`
   - supplier should later be notified that a customer created a reservation/order for their linked tour/offer.

This block should prepare:
- read-only payload builder;
- safe supplier contact resolution usage;
- outbox/pending record foundation;
- dedupe/idempotency key;
- audit fields;
- fail-safe missing-contact handling;
- no personal customer data.

---

## Hard constraints

Must preserve:

- Layer A remains booking/payment/order/reservation/seats truth.
- PaymentReconciliationService remains payment confirmation authority.
- TemporaryReservationService remains reservation/seat authority.
- Supplier notification foundation must not mutate orders/payments/reservations/tours/seats.
- Supplier notification foundation must not confirm payment.
- Supplier notification foundation must not expose customer personal data.
- No Telegram messages are sent in this block.
- No Telegram channel publish in this block.
- No scheduler/worker execution in this block.
- No passenger manifest.
- No B11 rewrite.
- No fake availability.
- No fake order/payment status.
- No hardcoded production chat ids.

---

## Step 1 — Inspect existing outbox/notification patterns

Search for:

```bash
grep -R "NotificationOutbox" -n app tests docs || true
grep -R "notification_outbox" -n app tests docs || true
grep -R "outbox" -n app/models app/services app/repositories app/schemas app/api tests | head -300 || true
grep -R "telegram_idempotency" -n app tests docs || true
grep -R "idempotency" -n app/models app/services app/repositories app/schemas app/api tests | head -300 || true
grep -R "SupplierTelegramContact" -n app tests docs || true
grep -R "supplier_telegram_contact" -n app tests docs || true
grep -R "primary_telegram_user_id" -n app tests docs || true
grep -R "publish" -n app/services app/api app/bot tests | head -300 || true
grep -R "TemporaryReservationService" -n app tests docs || true
grep -R "PaymentEntryService" -n app tests docs || true