# CURSOR_PROMPT_S1A_READ_ONLY_SUPPLIER_DEPARTURE_PASSENGER_COUNTS

You are continuing the existing Tours_BOT project.

This is NOT a new project, NOT a rewrite, and NOT a redesign.

## Cursor mode

Agent

## Block name

S1A — Read-Only Passenger Counts per Supplier / Tour / Departure

## Execution mode

Functional-block mode.

Reason:
- This block creates read-only operational visibility.
- It does not mutate Layer A booking/payment/order/reservation state.
- It does not send supplier notifications.
- It does not expose passenger manifests.
- It does not publish to Telegram channel.
- It does not create scheduler/worker behavior.

This follows P0:

S1 — Supplier Departure Operations & Passenger Count Notifications

Purpose:
- prepare supplier departure operations by reading aggregated passenger counts from Layer A operational truth.

Future subblocks:
- S1B — Supplier Telegram Contact Mapping
- S1C — Supplier Notification After Publish / Order
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
9. latest A6 / supplier-offer / execution-link / B11 / admin operation docs if present

If `docs/OPERATIONAL_AUTOMATION_ROADMAP.md` is missing, do not recreate it. Mention it in the report and use `P0_OPERATIONAL_AUTOMATION_ROADMAP_CHECKPOINT.txt` as policy source.

---

## Goal

Implement the first safe S1 step:

Create read-only operational passenger count visibility per supplier / tour / departure.

This block should allow admin/operator to see aggregated passenger counts for departures connected to supplier operations.

The result must be safe enough to become the future basis for supplier notifications, but this block must NOT send supplier notifications yet.

---

## Required behavior

Create a read-only service/model/API/admin visibility layer that can answer:

For a given supplier / supplier offer / linked tour / departure:

- how many active passenger seats are reserved
- how many are paid / confirmed
- how many are reserved but unpaid
- how many are cancelled / expired / not active
- tour capacity if available
- current remaining capacity if available
- departure datetime
- tour title/code
- supplier / supplier offer reference if linked
- readiness warnings if count cannot be resolved safely

Use existing Layer A order/tour/payment/reservation truth only.

Do not create new business truth.

---

## Count semantics

Use explicit count labels. Suggested fields:

```python
total_orders_count
active_orders_count
reserved_unpaid_orders_count
paid_confirmed_orders_count
cancelled_orders_count

active_passenger_count
reserved_unpaid_passenger_count
paid_confirmed_passenger_count
cancelled_passenger_count

capacity
seats_available
remaining_capacity
load_percentage