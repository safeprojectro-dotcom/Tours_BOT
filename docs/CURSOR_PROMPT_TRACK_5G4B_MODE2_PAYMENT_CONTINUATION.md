Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после уже принятого и реализованного Mode 2 executable self-serve slice.

Не начинай заново.
Не предлагай новую архитектуру.
Не смешивай Mode 2 и Mode 3.
Не переоткрывай RFQ/bridge.
Не трогай payment reconciliation.
Не делай новый payment stack.

## Continuity base (обязательна)

Уже подтверждено:
- Layer A booking/payment truth сохраняется
- `TemporaryReservationService` остаётся единственным hold path
- `PaymentEntryService` остаётся единственным payment-start path
- Mini App должен оставаться thin delivery layer над существующими сервисами
- business rules только в service layer
- repository layer persistence-only
- UI не дублирует policy

Это согласуется с текущим handoff: следующий safe step в Mini App после reserve action — payment screen / payment start, reusing existing service layer, без дублирования правил в Flet. :contentReference[oaicite:0]{index=0}  
Это же соответствует Phase 5 plan: Mini App должен поддерживать reserve seats и start payment, а payment screen должен показывать amount, timer и transition into payment scenario. 

## Что уже считается завершённым

Считать уже принятым и не переоткрывать:
- Track 5a–5f v1
- Track 5g, 5g.1, 5g.2, 5g.3, 5g.4, 5g.4a
- Mode 2 strict virgin capacity rule уже принят и реализован:
  - self-serve only if `seats_available == seats_total`
  - fixed `seats_count = seats_total`
  - partial inventory => assisted/manual catalog path
  - not RFQ fallback

Уже реализовано:
- catalog-specific policy fields
- Mode 2 self-serve hold gate for virgin capacity
- Mini App preparation / booking glue for fixed whole-bus seats_count
- partial bus blocks self-serve
- existing per-seat flow remains intact
- no migrations were added in that slice

## Exact next safe step

Implement the next narrow slice:

# Track 5g.4b / Mode 2 payment continuation

### Goal
After a successful Mode 2 whole-bus temporary reservation, route the user through the same existing payment-entry path as any Layer A order, and surface the correct payment/timer state in Mini App.

This is a continuation of the already implemented Mode 2 reserve slice.
Do not redesign reserve semantics.
Do not redesign pricing.
Do not redesign payment provider integration.

## What must be implemented

### 1. Payment continuation after successful Mode 2 hold
For a valid Mode 2 order created through the existing whole-bus self-serve path:
- user can continue to payment via existing `PaymentEntryService`
- same `Order`
- same payment session semantics
- same reuse behavior for pending payment entry if already created
- no new payment architecture

### 2. Mini App payment screen / entry behavior
Ensure Mini App can show and/or navigate into payment state for Mode 2 consistent with Phase 5 UX:
- reservation reference
- amount due
- reservation expiry / timer
- payment status summary
- primary CTA: `Pay Now`
- provider-neutral copy only
- no fake payment success
- no invented status transitions

This follows Mini App UX payment rules: amount, timer, payment status summary, `Pay Now`, and backend-confirmed state only.   
Timer must stay backend-owned and remain visible while reservation is active. :contentReference[oaicite:3]{index=3}

### 3. Preserve current Mode 2 guardrails
If self-serve reserve was not allowed for Mode 2, this slice must not create a backdoor into payment.
Payment continuation is only for a valid already-created order.

### 4. Keep UI thin
If new Mini App API endpoints are needed:
- make them minimal
- no business logic in route/UI
- no reimplementation of payment-entry checks in Flet

## Likely files/modules to touch

Only if needed:
- `app/services/mini_app_payment*.py` or equivalent thin adapter/service
- `app/services/mini_app_booking.py`
- `app/api/routes/mini_app.py`
- `mini_app/app.py`
- maybe additive response schemas for payment entry / booking status
- focused tests for Mini App payment continuation glue

Avoid broad touching of:
- `PaymentReconciliationService`
- RFQ bridge services
- supplier marketplace flows
- admin flows
- private bot flows unless absolutely required

## What must NOT change

Do not change:
- `PaymentEntryService` semantics
- `PaymentReconciliationService`
- Mode 1 per-seat behavior
- bridge/payment-eligibility for RFQ
- 5f v1 customer multi-quote visibility
- payment provider architecture
- waitlist
- handoff/operator workflow
- Mini App auth/init expansion unless strictly needed for a tiny existing-stub-compatible path
- my bookings full implementation if it is not required for this narrow slice

## Before coding
Output briefly:
1. current state
2. what is already completed
3. exact next safe step
4. files likely to change
5. risks
6. what remains postponed

## Implementation constraints
- additive and narrow only
- no migration unless absolutely necessary; prefer none
- no broad copy rewrite
- keep provider-neutral payment UX
- backend remains source of truth for reservation expiry and payment state
- preserve idempotent / reuse semantics for existing payment entry

## Tests required
Add focused tests only for the new slice:
- valid Mode 2 whole-bus order can enter payment via existing payment-entry path
- repeated payment-entry call reuses existing pending session if that is current Layer A behavior
- partial/assisted-only Mode 2 does not gain any backdoor through payment continuation
- existing Mode 1 payment continuation still works
- no RFQ/bridge coupling introduced

Use narrow API/service tests, not a rewrite of earlier payment tests.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what behavior is now supported
6. compatibility notes
7. postponed items

## Extra continuity note
The earlier incidental bot-side summary support for virgin charter must not be expanded into a new private-bot product commitment in this slice.
This step is about Mini App payment continuation only.