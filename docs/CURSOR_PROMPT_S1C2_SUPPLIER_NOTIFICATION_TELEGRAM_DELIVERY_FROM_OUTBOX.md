# CURSOR_PROMPT_S1C2_SUPPLIER_NOTIFICATION_TELEGRAM_DELIVERY_FROM_OUTBOX

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a redesign.

## Cursor mode

Agent

## Block name

S1C-2 — Supplier Notification Telegram Delivery from Outbox

## Execution mode

Narrow-step mode.

Reason:
- This block performs actual Telegram supplier notification delivery.
- Telegram send is an external visible side effect.
- Delivery must happen only from the S1C-1 supplier_notification_outbox.
- No automatic publish/order hooks in this block.
- No scheduler/worker automation in this block.
- No Layer A mutation.

---

## Context

S1A completed:
- read-only departure passenger counts.

S1B completed:
- supplier Telegram contact resolver using `Supplier.primary_telegram_user_id`.

S1C-1 completed:
- `supplier_notification_outbox` table/model/migration.
- supplier notification payload foundation.
- event types:
  - `supplier_offer_published`
  - `supplier_order_created`
- pending/skipped records.
- deterministic idempotency.
- no Telegram send.

S1C-2 must now implement controlled delivery from outbox to Telegram.

---

## Goal

Implement actual Telegram delivery for existing `supplier_notification_outbox` records with status `pending_dispatch`.

This block should allow an admin/manual service call or narrow service function to process one outbox item safely.

Do NOT add automatic triggers.
Do NOT add scheduler.
Do NOT wire publish/order events yet.

---

## Source documents / files to inspect first

Inspect:

1. `docs/CHAT_HANDOFF.md`
2. `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
3. `P0_OPERATIONAL_AUTOMATION_ROADMAP_CHECKPOINT.txt`
4. S1C-1 files:
   - `app/models/supplier_notification_outbox.py`
   - `app/repositories/supplier_notification_outbox.py`
   - `app/schemas/supplier_notification_outbox.py`
   - `app/services/supplier_notification_outbox_service.py`
   - `tests/unit/test_supplier_notification_outbox_s1c1.py`
5. Existing Telegram delivery / bot send patterns:
   - notification delivery services
   - Telegram adapter/service
   - bot initialization patterns
   - existing outbox processing services
   - supplier execution Telegram send/idempotency patterns if present

If `docs/OPERATIONAL_AUTOMATION_ROADMAP.md` is missing, do not recreate it. Use P0 checkpoint as source policy.

---

## Hard constraints

Must preserve:

- Layer A remains booking/payment/order/reservation/seats truth.
- PaymentReconciliationService remains payment confirmation authority.
- TemporaryReservationService remains reservation/seat authority.
- Supplier notification delivery must not mutate orders/payments/reservations/tours/seats.
- No publish/order automatic hooks.
- No scheduler/worker automation.
- No Telegram channel publish.
- No passenger manifest.
- No customer personal data.
- No B11 routing change.
- No fake payment/order/availability state.
- No hardcoded production chat ids.

---

## Step 1 — Inspect existing delivery patterns

Search for:

```bash
grep -R "NotificationOutbox" -n app tests docs || true
grep -R "notification_outbox_processing" -n app tests docs || true
grep -R "send_message" -n app tests docs | head -300 || true
grep -R "Bot(" -n app tests docs | head -200 || true
grep -R "telegram" -n app/services app/bot app/api tests | head -300 || true
grep -R "supplier_notification_outbox" -n app tests docs || true
grep -R "delivered" -n app/models app/services app/repositories tests | head -300 || true
grep -R "failed" -n app/models app/services app/repositories tests | head -300 || true