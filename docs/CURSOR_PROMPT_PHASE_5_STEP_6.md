# Phase 5 / Step 6 — Mini App My Bookings / Booking Status View

Use:
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/MINI_APP_UX.md`
- `docs/TESTING_STRATEGY.md`
- `docs/AI_ASSISTANT_SPEC.md`
- `docs/AI_DIALOG_FLOWS.md`
- `docs/TECH_SPEC_TOURS_BOT.md`

Implement **Phase 5 / Step 6** exactly within this scope.

## Current confirmed checkpoint

Project: `Tours_BOT`

Current approved checkpoint:
- **Phase 5 / Step 5 completed**
- commit: `929988f`
- message: `feat: add mini app reservation creation and payment start`

Already completed before this step:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed through temporary reservation creation in private bot
- Phase 4 payment/reconciliation/webhook/expiry/notification foundations completed
- Phase 5 / Step 1 completed: `docs/MINI_APP_UX.md`
- Phase 5 / Step 2 completed: Mini App foundation + catalog + filters
- Phase 5 / Step 3 completed: Mini App read-only tour detail
- Phase 5 / Step 4 completed: Mini App reservation preparation UI only
- Phase 5 / Step 5 completed: Mini App real temporary reservation creation + payment start

## Goal of this step

Deliver the next safe Phase 5 slice:
- **Mini App My Bookings screen**
- **Mini App Booking Detail / Status View**
- user-friendly display of:
  - active temporary reservations
  - confirmed bookings if present
  - expired / no-payment reservation history in a human-readable way
  - payment status
  - reservation expiry when relevant

This step must reuse already implemented read/service-layer foundations:
- `OrderReadService`
- `OrderSummaryService`
- `PaymentSummaryService`
- any existing language-aware/user profile read services already in the project

Do **not** duplicate booking/payment rules in Flet/UI.

---

## Required before coding

Before writing code, output a short implementation note with:

1. **Current Phase**
2. **Next Safe Step**
3. **What you will implement in this step**

Then also briefly list:
1. what Steps 1–5 already delivered
2. how this step maps to `docs/IMPLEMENTATION_PLAN.md` Phase 5 Included Scope / Done-When
3. what remains explicitly postponed after this step

Keep this pre-code summary concise.

---

## Exact scope

### Implement
1. My Bookings list for Mini App
   - show the current user's bookings/orders
   - keep it mobile-first and simple
   - show user-friendly booking/payment state labels
   - include active temporary reservations and confirmed bookings
   - include expired/no-payment items only if they can be shown clearly and without exposing confusing raw backend status combinations

2. Booking Detail / Status View
   - open from a selected booking
   - show:
     - tour summary
     - seats count
     - boarding point
     - amount
     - booking status summary
     - payment status summary
     - reservation timer when still active
   - state-based CTA:
     - `Pay Now` when reservation is active and unpaid
     - `Browse Tours` when reservation expired
     - `Back to Bookings` when booking is already complete

3. Minimal Mini App API/UI glue
   - add only the narrowest API/read adapter layer needed
   - keep service layer as the owner of state interpretation inputs
   - if possible, centralize user-facing state translation in a narrow Mini App-facing service instead of scattering it in UI

4. User-facing status translation
   - current backend expiry semantics are still:
     - `booking_status=reserved`
     - `payment_status=unpaid`
     - `cancellation_status=cancelled_no_payment`
   - do not expose this raw combination directly to the user
   - present it as a clear user-facing expired/no-payment state

---

## Strict scope guardrails

### Do not implement in this step
- waitlist workflow
- handoff/operator workflow
- Mini App auth/initData expansion unless a tiny stub is strictly required
- provider-specific checkout integration
- refund flow
- admin changes
- group bot changes
- content workflows
- analytics expansion
- payment reconciliation UI beyond current status display

### Do not change
- repository/service/UI boundaries
- payment reconciliation as the only source of truth for paid-state transition
- PostgreSQL-first assumptions
- reservation expiry policy unless absolutely required
- existing seat decrement / seat restoration ownership model
- current multilingual fallback model

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

### My Bookings
- simple, mobile-first list
- each item should clearly show:
  - tour title
  - date
  - amount
  - booking state
  - payment state
- dominant CTA per item: `Open`

### Booking Detail / Status View
- if active unpaid reservation:
  - show timer
  - show `Pay Now`
- if expired:
  - show expired/no-payment meaning clearly
  - show `Browse Tours`
- if already confirmed:
  - show confirmed state without payment CTA

### Important UX constraint
Current raw backend status semantics can be confusing for expired reservations.
The Mini App must translate them into a human-readable state and must not dump raw enum combinations into the UI.

---

## Testing expectations

Follow `docs/TESTING_STRATEGY.md`:
- define affected modules
- define risks
- define minimal tests
- implement the smallest safe step

### Add focused tests only for Mini App-specific read/status glue
Examples:
- bookings list endpoint returns only the current user's bookings
- booking detail endpoint returns expected summary/state data
- active unpaid reservation includes expiry/timer data
- expired reservation maps into user-friendly expired/no-payment state
- no duplication of payment confirmation logic

### Do not
- rewrite or duplicate earlier Phase 3–5 test coverage
- broaden into unrelated integration suites

---

## Suggested implementation shape

Expected direction:
- add Mini App read endpoints for bookings list and booking detail/status
- add a narrow Mini App-facing service/adapter for user-visible booking state
- update Flet Mini App with:
  - My Bookings screen
  - Booking Detail / Status View
  - state-based CTA routing

Keep naming consistent with the current codebase.
Do not redesign the whole Mini App structure if a narrow extension is enough.

---

## Important continuity notes

From `docs/CHAT_HANDOFF.md` and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, preserve these assumptions:
- reservation creation already reduces `seats_available`
- expiry worker restores seats for eligible unpaid expired reservations
- payment provider is still mock/provider-agnostic
- payment reconciliation must remain the single place that can confirm paid state
- current expired reservation semantics must be translated into user-facing meaning in Mini App
- current Mini App still uses dev assumptions for Telegram user identity

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

This is a **safe, narrow Step 6 slice** only:
- Mini App My Bookings
- Mini App Booking Detail / Status View

Do not expand the project beyond that.