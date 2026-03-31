# Phase 5 / Step 5 — Mini App Temporary Reservation Creation + Payment Start

Use:
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/MINI_APP_UX.md`
- `docs/TESTING_STRATEGY.md`
- `docs/AI_ASSISTANT_SPEC.md`
- `docs/AI_DIALOG_FLOWS.md`
- `docs/TECH_SPEC_TOURS_BOT.md`

Implement **Phase 5 / Step 5** exactly within this scope.

## Current confirmed checkpoint

Project: `Tours_BOT`

Current approved checkpoint:
- **Phase 5 / Step 4 completed**
- commit: `a9342cc`
- message: `feat: add mini app reservation preparation ui`

Already completed before this step:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed through temporary reservation creation in private bot
- Phase 4 payment/reconciliation/webhook/expiry/notification foundations completed
- Phase 5 / Step 1 completed: `docs/MINI_APP_UX.md`
- Phase 5 / Step 2 completed: Mini App foundation + catalog + filters
- Phase 5 / Step 3 completed: Mini App read-only tour detail
- Phase 5 / Step 4 completed: Mini App reservation preparation UI only

## Goal of this step

Deliver the next safe Phase 5 slice:
- **Mini App real temporary reservation creation**
- **Mini App payment start / continue-to-payment**
- show **reservation timer / amount / expiry** where needed for reservation and payment screens

This step must reuse the already implemented service-layer foundations:
- `TemporaryReservationService`
- `PaymentEntryService`

Do **not** duplicate booking or payment business rules in Flet/UI.

---

## Required before coding

Before writing code, output a short implementation note with:

1. **Current Phase**
2. **Next Safe Step**
3. **What you will implement in this step**

Then also briefly list:
1. what Steps 1–4 already delivered
2. how this step maps to `docs/IMPLEMENTATION_PLAN.md` Phase 5 Included Scope / Done-When
3. what remains explicitly postponed after this step

Keep this pre-code summary concise.

---

## Exact scope

### Implement
1. Real temporary reservation creation from Mini App
   - convert the current preparation flow into a real reserve action
   - create the reservation/order through existing backend service logic
   - do not reimplement reservation rules in route/UI code

2. Payment start / continue-to-payment from Mini App
   - create or reuse payment entry through existing `PaymentEntryService`
   - keep provider-neutral behavior
   - do not mark anything as paid here
   - do not change reconciliation flow

3. Reservation/payment UI state wiring
   - reservation success state should show:
     - reservation reference if available
     - amount
     - reservation expiry
     - timer-friendly data
   - payment screen/state should show:
     - amount due
     - reservation expiry
     - payment reference/session reference if available
     - `Pay Now` as dominant CTA

4. Minimal Mini App API/UI glue only
   - add only the thinnest new route/service adapter layer needed
   - keep business rules in existing services
   - keep routes thin
   - keep UI mobile-first and aligned with `docs/MINI_APP_UX.md`

---

## Strict scope guardrails

### Do not implement in this step
- waitlist workflow
- handoff/operator workflow
- Mini App auth/init expansion unless a tiny stub is strictly required for this narrow slice
- my bookings screen
- booking history screen
- help/operator live workflow
- admin changes
- group bot changes
- content workflows
- provider-specific payment integration
- refund flow
- any new business-policy redesign

### Do not change
- repository/service/UI boundaries
- payment reconciliation as the only source of truth for paid-state transition
- PostgreSQL-first assumptions
- reservation expiry policy unless absolutely required
- existing seat decrement / seat restoration ownership model
- existing multilingual fallback model

---

## Architectural rules

- service layer owns workflow/business rules
- repositories remain persistence-oriented only
- route layer must stay thin
- Flet/UI must stay thin
- timer semantics must remain backend-owned
- unsupported flows must not be shown as implemented
- state shown in UI must come from backend/service results, not UI guesses
- no fake urgency
- no invented payment success
- no invented reservation/payment statuses

---

## UX rules for this step

Follow `docs/MINI_APP_UX.md` closely.

### Reservation screen
- dominant CTA: `Confirm Reservation`
- must clearly show that reservation is temporary
- must show expiry/timer data from backend
- must lead cleanly into payment

### Payment screen
- dominant CTA: `Pay Now`
- must stay provider-neutral
- must show amount and expiry
- must not claim payment success before confirmed backend state exists

### Mobile-first
- keep the UI simple
- no clutter
- no parallel competing primary actions
- keep the flow step-by-step:
  - preparation
  - confirm reservation
  - continue to payment

---

## Testing expectations

Follow `docs/TESTING_STRATEGY.md`:
- define affected modules
- define risks
- define minimal tests
- implement the smallest safe step

### Add focused tests only for Mini App-specific glue
Examples:
- reserve endpoint creates temporary reservation via existing service
- payment-start endpoint calls/reuses existing payment-entry behavior correctly
- returned payload includes amount / expiry / timer data expected by Mini App
- invalid/unavailable cases handled without duplicating business logic

### Do not
- rewrite or duplicate earlier Phase 3–4 test coverage
- broaden into unrelated integration suites

---

## Suggested implementation shape

Use the existing Step 4 flow as the base.

Expected direction:
- extend Mini App backend endpoints beyond preparation-only
- add a real reserve action endpoint
- add a payment-start endpoint
- update Mini App UI to call those endpoints
- route/UI returns and displays service-owned reservation/payment summary data

Keep naming consistent with the current codebase.
Do not redesign the whole Mini App structure if a narrow extension is enough.

---

## Important continuity notes

From `docs/CHAT_HANDOFF.md` and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, preserve these assumptions:
- reservation creation already reduces `seats_available`
- expiry worker restores seats for eligible unpaid expired reservations
- payment provider is still mock/provider-agnostic
- payment reconciliation must remain the single place that can confirm paid state
- expired reservation semantics are currently:
  - `booking_status=reserved`
  - `payment_status=unpaid`
  - `cancellation_status=cancelled_no_payment`
- UI must translate backend state into user-friendly meaning, not expose raw confusing state combinations

---

## Deliverable format after implementation

After coding, report exactly:

1. **files changed**
2. **tests run**
3. **results**
4. **what remains postponed**

Be explicit and keep the report narrow.

---

## Reminder

This is a **safe, narrow Step 5 slice** only:
- Mini App temporary reservation creation
- Mini App payment start

Do not expand the project beyond that.