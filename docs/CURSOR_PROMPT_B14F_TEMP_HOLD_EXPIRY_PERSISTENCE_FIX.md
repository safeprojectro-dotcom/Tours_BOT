# CURSOR_PROMPT_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX

Implement a narrow fix for temporary hold expiry persistence and inventory release.

## Context

B14E diagnosed a production-relevant issue.

Smoke facts:

- Supplier Offer #12
- Tour #6
- tour_code = `B10-SO12-04fb1f`
- execution_link_id = 5
- boarding_point_id = 15
- seats_total = 10

During manual Mini App smoke, two temporary reservations were created:

Order #52:
- seats_count = 1
- booking_status = `reserved`
- payment_status = `awaiting_payment`
- cancellation_status = `active`
- lifecycle_kind = `active_temporary_hold`
- reservation_expires_at = `2026-05-10T17:52:43.977638Z`

Order #53:
- seats_count = 2
- booking_status = `reserved`
- payment_status = `awaiting_payment`
- cancellation_status = `active`
- lifecycle_kind = `active_temporary_hold`
- reservation_expires_at = `2026-05-10T17:54:19.743027Z`
- open handoff #86 exists

After expiry time:
- Tour #6 still had `seats_available = 7`
- Orders #52/#53 still showed `active_temporary_hold`

B14E findings:

- Expiry logic exists in `app/services/reservation_expiry.py` / `ReservationExpiryService`.
- It can mark expired holds as no-payment/cancelled and restore seats.
- Worker exists: `app/workers/reservation_expiry.run_once`, but production does not automatically run it from app startup in-repo.
- Lazy expiry is called from several Mini App GET flows, but some handlers call expiry without committing the session, so changes may roll back.
- Admin reads do not run lazy expiry and use persisted order fields.
- There is no dedicated admin expire endpoint.
- Existing `mark-cancelled-by-operator` can release seats, but uses operator-cancel semantics, not no-payment expiry semantics.

## Goal

Fix the code so lazy expiry persistence is reliable when expired holds are encountered through existing safe request paths.

Minimum required outcome:

- When a request path calls lazy expiry and expired holds are found, the changes must be committed.
- Expired temporary holds should release seats via `ReservationExpiryService`.
- Existing reservation/payment/order architecture must not be redesigned.
- Do not add a scheduler in this step unless absolutely necessary; document scheduler as separate ops/future work if needed.
- Do not mutate production orders directly from Cursor.

## Required inspection

Read docs:

- `docs/B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC.md`
- `docs/HANDOFF_B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC_TO_NEXT_STEP.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/MINI_APP_UX.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/TESTING_STRATEGY.md`

Inspect code:

- `app/services/reservation_expiry.py`
- `app/workers/reservation_expiry.py`
- `app/api/routes/mini_app.py`
- `app/services/mini_app_reservation_preparation_service.py`
- `app/services/private_reservation_preparation_service.py`
- `app/services/payment_entry_service.py`
- `app/services/order_admin_read_service.py` or equivalent admin order lifecycle code
- repositories touching:
  - orders
  - tours
  - seats_available
- tests for:
  - reservation expiry
  - temporary reservation
  - Mini App preparation
  - payment entry
  - admin orders lifecycle

Search for:

- `lazy_expire_due_reservations`
- `ReservationExpiryService`
- `reservation_expires_at`
- `active_temporary_hold`
- `seats_available`
- `cancelled_no_payment`
- `awaiting_payment`
- `get_preparable_tour`
- `preparation`
- `reservation-overview`
- `payment-entry`

## Implementation requirements

### 1. Preserve central expiry semantics

Do not duplicate expiry rules in routes.

Use existing `ReservationExpiryService` or a thin helper around it.

The service should remain the source of truth for:

- which orders are eligible;
- how seats are restored;
- how order/payment/cancellation fields are updated.

### 2. Make lazy expiry commit-safe

Find request paths that currently call lazy expiry but do not persist it.

Implement the narrowest safe fix.

Acceptable approaches:

#### Preferred approach A

Introduce or reuse a small helper that does:

- run lazy expiry;
- if any rows changed, `session.commit()`;
- continue with normal read/preparation/payment-entry flow.

Make sure this helper is used only in places where committing expiry is safe before continuing.

#### Alternative approach B

Add explicit `session.commit()` after lazy expiry in specific handlers/services that are already intended to mutate expiry state.

Avoid committing unrelated pending user changes.

### 3. Do not weaken guards

Do not:

- bypass reservation expiry;
- bypass payment checks;
- make expired orders payable;
- alter seat decrement logic for new holds;
- change TemporaryReservationService except where directly required by tests.

### 4. Consider payment-entry path

B14E found that `PaymentEntryService` may reject expired orders but not call expiry/release.

Inspect and decide if B14F should:

- call central expiry before payment-entry creation/read; or
- leave it for a separate B14G prompt.

If included, it must be tested.

### 5. Admin reads

Admin read currently reports persisted lifecycle.

Do not redesign admin lifecycle in this step unless very small and safe.

It is acceptable to document that admin reads are not expiry executors.

### 6. Production orders #52/#53

Do not write code that hardcodes or special-cases #52/#53.

Do not call production APIs.

After deployment, existing expired smoke orders should be handled by:

- hitting a committing lazy-expiry path; or
- running the worker; or
- a future admin/manual expiry endpoint if needed.

Document the recommended safe production follow-up.

### 7. Tests

Add or update tests proving:

1. Expired temporary hold releases seats when lazy expiry is invoked through the chosen path.
2. The order is no longer classified as active temporary hold after expiry persistence.
3. `reservation_expires_at` is cleared or persisted according to existing `ReservationExpiryService` semantics.
4. `seats_available` is restored exactly once.
5. Non-expired active holds are not changed.
6. Payment-entry path cannot proceed for expired holds; if B14F makes it expire/release, test that too.
7. Regression: Mini App preparation still works for valid open tours.
8. Regression: creating a new reservation still decrements seats as before.

Run focused tests. Suggested candidates, adjust names to actual repo:

- reservation expiry tests
- temporary reservation tests
- mini app reservation preparation tests
- payment entry tests
- admin order lifecycle tests

## Documentation updates

Update:

- `docs/B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC.md`
  - Add B14F implementation follow-up note.
- `docs/CHAT_HANDOFF.md`
  - Add B14F bullet.
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
  - Update stale holds item:
    - lazy expiry persistence fixed if implemented;
    - scheduler/worker still separate if not implemented;
    - production #52/#53 need post-deploy cleanup/check.

Create:

- `docs/HANDOFF_B14F_TEMP_HOLD_EXPIRY_PERSISTENCE_FIX_TO_NEXT_STEP.md`

The handoff must include:

- what was fixed;
- exact code paths changed;
- tests run;
- what remains open;
- production follow-up for orders #52/#53;
- whether scheduler/worker is still required;
- next recommended prompt.

## Forbidden

Do not:

- call production APIs;
- mutate production data;
- hardcode order IDs #52/#53;
- create/cancel orders in production;
- create reservations in production;
- create payments;
- publish/retry/resend;
- mutate execution links;
- change Supplier Offer / showcase CTA behavior;
- add broad scheduler/startup behavior unless explicitly justified and tested;
- weaken Layer A / reservation / payment guards.

## After completion report

Return:

1. pre-code root cause summary;
2. files changed;
3. implementation summary;
4. exact expiry paths fixed;
5. tests added/changed;
6. tests run and results;
7. production follow-up recommendation for Orders #52/#53;
8. whether scheduler/worker is still needed;
9. next recommended prompt name;
10. `git status --short`;
11. `git diff --stat`;
12. confirmations:
    - no production API calls;
    - no production data mutation;
    - no hardcoded #52/#53;
    - no publish/retry/resend;
    - no execution-link mutation;
    - no orders/payments/reservations created by this work;
    - no CTA behavior change;
    - no weakening of reservation/payment guards.