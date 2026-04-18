Продолжаем ЭТОТ ЖЕ проект Tours_BOT как continuation после Track 5g.4a.

Нельзя:
- переизобретать архитектуру
- смешивать Mode 2 и Mode 3
- трогать RFQ bridge/payment eligibility logic
- делать новый booking/payment stack
- делать schema overhaul
- расширять scope beyond narrow implementation slice

## Current state you must accept
Layer A booking/payment path already exists and is authoritative:
- temporary reservation is created through existing `TemporaryReservationService`
- payment start is created through existing `PaymentEntryService`
- Mini App foundation already exists: catalog, filters, read-only detail, reservation preparation
- business rules must stay in service layer
- repository layer remains persistence-only
- UI/Mini App must stay thin

Accepted commercial model:
- Mode 1 = `supplier_route_per_seat`
- Mode 2 = `supplier_route_full_bus`
- Mode 3 = `custom_bus_rental_request`
- Mode 2 != Mode 3
- standalone catalog Mode 2 must NOT use RFQ/bridge flow

## What 5g.4a already decided
Accepted final rule for Mode 2 self-serve whole-bus hold:

### Strict virgin capacity model
Allow self-serve whole-bus hold only if:
- `tour.seats_available == tour.seats_total`

When allowed:
- `seats_count = tour.seats_total`

After successful hold:
- `seats_available -> 0` through existing Layer A behavior

When not allowed:
- self-serve Mode 2 must be blocked
- fallback is assisted/manual catalog path
- NOT RFQ fallback

Important:
- no new pricing logic in this step
- no second payment architecture
- no bridge/payment-eligibility reuse from Mode 3
- existing payment-entry remains the only payment-start path

## Exact next safe implementation step
Implement narrow Mode 2 executable slice.

### Goal
Enable self-serve Mode 2 reserve + existing payment-entry only when whole-bus virgin-capacity predicate passes.

### Required behavior
1. Introduce/extend policy logic so that for `supplier_route_full_bus`:
   - self-serve allowed only when `seats_available == seats_total`
   - required reservation quantity is fixed to `seats_total`
   - if bus is partially consumed, self-serve is blocked

2. Reuse existing Layer A reservation creation:
   - no new order model
   - no new reservation model
   - same `TemporaryReservationService`

3. Reuse existing payment-entry after hold:
   - same Order
   - same `PaymentEntryService`
   - no alternate payment flow

4. Mini App preparation/detail behavior must reflect this:
   - Mode 2 self-serve path should not expose misleading arbitrary seat picker when whole-bus mode is active
   - if self-serve allowed, quantity is effectively fixed to full capacity
   - if not allowed, show assisted/manual state, not RFQ/custom request framing

## Files/modules likely to touch
Expected likely areas only if needed:
- `app/services/tour_sales_mode_policy*.py` or equivalent policy service
- `app/services/mini_app_reservation_preparation.py`
- `app/services/mini_app_booking*.py`
- Mini App detail/preparation response models if they need additive fields
- minimal API routes for preparation/reservation if existing routes need additive output
- tests for policy/preparation/booking glue

## Must not change
- RFQ / custom request / booking bridge flows
- payment reconciliation logic
- payment-entry semantics
- existing Mode 1 per-seat flow
- 5f v1 customer multi-quote visibility
- general marketplace architecture
- admin redesign
- private bot redesign unless required by the narrow slice

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact next safe step
4. files likely to change
5. risks
6. what remains postponed

## Implementation guidance
- keep changes additive and narrow
- keep policy in service layer, not in UI
- if needed, expose explicit preparation flags like:
  - `self_serve_allowed`
  - `fixed_seats_count`
  - `assisted_only`
  but only if actually needed for thin UI/API behavior
- avoid big refactors
- no migration unless absolutely necessary; prefer none

## Tests required
Add focused tests only:
- Mode 2 full bus + virgin capacity -> self-serve allowed
- Mode 2 full bus + partial inventory -> self-serve blocked
- booking path uses `seats_count = seats_total`
- existing per-seat flow remains unaffected
- no RFQ bridge dependency appears in standalone Mode 2 path

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what behavior is now supported
6. compatibility notes
7. postponed items