# CURSOR_PROMPT_S1B_SUPPLIER_TELEGRAM_CONTACT_MAPPING

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a redesign.

## Cursor mode

Agent

## Block name

S1B — Supplier Telegram Contact Mapping

## Execution mode

Narrow-step mode.

Reason:
- S1B prepares future supplier Telegram notifications.
- Supplier notification send is an external visible side effect.
- Supplier contact mapping touches permission/privacy assumptions.
- This block must be minimal, safe, and reversible.
- No supplier notification should be sent in this block unless an existing safe dry-run mechanism already exists and remains non-sending.

---

## Context

S1A is completed, committed, and pushed:

- read-only departure passenger counts per supplier / tour / departure;
- admin GET routes added;
- no supplier notification send;
- no passenger manifest;
- no public Telegram publish;
- no Layer A mutation.

S1B must now prepare the smallest safe way to resolve a supplier Telegram contact/chat for future notifications.

This block supports future S1 steps:

- S1C — Supplier Notification After Channel Publish / Order
- S1D — Admin-Gated Last-Seats Operational Publish
- S1E — Secure Passenger Manifest Design Gate

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
10. S1A files:
   - `app/services/admin_departure_passenger_counts_service.py`
   - `app/schemas/admin_departure_passenger_counts.py`
   - `tests/unit/test_admin_departure_passenger_counts.py`

If `docs/OPERATIONAL_AUTOMATION_ROADMAP.md` is missing, do not recreate it. Mention it in the report and use `P0_OPERATIONAL_AUTOMATION_ROADMAP_CHECKPOINT.txt` as policy source.

---

## Goal

Implement the smallest safe supplier Telegram contact mapping required for future supplier notifications.

The key question:

> Given a supplier / supplier offer / linked tour / order context, can the system safely resolve a supplier Telegram chat id/contact for future notification?

This block must NOT send supplier notifications yet.

---

## Required behavior

Create a read-only resolver that can answer:

- Does this supplier have a configured Telegram contact?
- Can a supplier offer resolve to a supplier Telegram contact?
- Can a tour resolve to a supplier Telegram contact only if existing safe relationships support it?
- Can an order resolve to a supplier Telegram contact only if existing safe relationships support it?
- If contact is missing, return a safe missing result instead of crashing.
- If relationship is ambiguous, return a warning / unresolved result instead of guessing.

---

## Hard constraints

Must preserve:

- Layer A booking/payment/order/reservation truth.
- PaymentReconciliationService remains payment confirmation authority.
- TemporaryReservationService remains reservation/seat authority.
- No supplier notification send in this block.
- No Telegram channel publish.
- No scheduler.
- No passenger manifest.
- No customer personal data.
- No order/payment/reservation mutation.
- No seat inventory mutation.
- No B11 rewrite.
- No fake supplier mapping.
- No hardcoded production chat id.
- No notification to arbitrary chat id.

---

## Step 1 — Inspect current data model and relationships

Search for:

```bash
grep -R "class Supplier" -n app tests docs || true
grep -R "supplier" -n app/models app/services app/repositories app/schemas app/api app/bot tests | head -300 || true
grep -R "telegram" -n app/models app/services app/repositories app/schemas app/api app/bot tests | head -300 || true
grep -R "chat_id" -n app tests docs || true
grep -R "telegram_user_id" -n app tests docs || true
grep -R "supplier_offer" -n app tests docs | head -300 || true
grep -R "execution_link" -n app tests docs | head -300 || true
grep -R "SupplierOfferExecutionLink" -n app tests docs || true
grep -R "SupplierOfferTourBridge" -n app tests docs || true