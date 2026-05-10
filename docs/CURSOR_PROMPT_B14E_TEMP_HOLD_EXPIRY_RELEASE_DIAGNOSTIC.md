# CURSOR_PROMPT_B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC

Read-only diagnostic first. Do not change code unless explicitly asked in a later prompt.

## Context

B13G/B14D smoke for Supplier Offer #12 / Tour #6 reached the Mini App reservation flow.

Known IDs:

- supplier_offer_id: 12
- tour_id: 6
- tour_code: `B10-SO12-04fb1f`
- execution_link_id: 5
- boarding_point_id: 15

B14D production remediation:

- Added boarding point #15 to Tour #6 via:
  - `POST /admin/tours/6/boarding-points`
- `GET /mini-app/tours/B10-SO12-04fb1f/preparation` now works.
- Preparation response includes:
  - boarding_points
  - seat_count_options
  - `sales_mode_policy.catalog_actionability_state = bookable`
  - `mini_app_catalog_reservation_allowed = true`

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
- has open handoff #86 from Mini App booking detail/support

Tour #6 after these holds:
- seats_total = 10
- seats_available = 7
- orders_count = 2

Problem:
After the stated `reservation_expires_at`, admin read still shows both orders as `active_temporary_hold`, and Tour #6 still has `seats_available = 7`.

OpenAPI search showed no obvious `/expire`, `/expiry`, `/cleanup`, `/release` endpoint. Existing order admin endpoints include:
- `/admin/orders/{order_id}/mark-cancelled-by-operator`
- `/admin/orders/{order_id}/mark-duplicate`
- `/admin/orders/{order_id}/mark-no-show`
- `/admin/orders/{order_id}/mark-ready-for-departure`
- `/admin/orders/{order_id}/move`

## Goal

Diagnose the temporary hold expiry / inventory release mechanism.

Answer:

1. Where is temporary reservation expiry supposed to happen?
2. Is there a service/job/function that scans expired holds?
3. Is it called automatically in production startup, background worker, scheduler, request path, or only manually?
4. Does admin order read compute lifecycle from persisted status only, or does it apply expiry logic?
5. Does payment-entry or reservation-overview path lazily expire holds?
6. Which function releases seats back to `tour.seats_available`?
7. Are expired holds supposed to change:
   - booking_status?
   - payment_status?
   - cancellation_status?
   - reservation_expires_at?
   - lifecycle_kind?
8. Is there a safe existing admin endpoint to expire/cancel these smoke orders and release inventory?
9. What is the safest remediation for existing smoke orders #52 and #53?
10. Is this a production configuration gap, missing scheduled worker, or missing code path?

## Required inspection

Read docs:
- `docs/CHAT_HANDOFF.md`
- `docs/MINI_APP_UX.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/TESTING_STRATEGY.md`
- `docs/B14D_TOUR6_BOARDING_REMEDIATION_AND_PREP_SMOKE_RUNBOOK.md`
- `docs/HANDOFF_B14D_TOUR6_BOARDING_REMEDIATION_AND_PREP_SMOKE_TO_NEXT_STEP.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Inspect code:
- temporary reservation service
- payment entry service
- order lifecycle/admin read services
- repositories handling orders and tours
- any scheduler/worker/startup cleanup
- Mini App reservation overview / payment entry routes
- admin order mutation routes

Search for:
- `reservation_expires_at`
- `active_temporary_hold`
- `expire`
- `expired`
- `release`
- `seats_available`
- `awaiting_payment`
- `mark-cancelled-by-operator`
- `cancelled`
- `duplicate`
- `no_show`
- `cleanup`
- `scheduler`
- `background`
- `TemporaryReservationService`

## Important safety

Do not:
- call production APIs;
- mutate production data;
- cancel orders;
- create orders;
- create reservations;
- create payments;
- publish/retry/resend;
- change execution links.

This is diagnostic only.

## Deliverable

Create:

`docs/B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC.md`

The diagnostic must include:

1. Context and smoke facts:
   - Tour #6
   - Orders #52 and #53
   - seats_available 10 → 7
2. Current expiry design found in code.
3. Whether expiry is automatic, lazy, manual, or missing.
4. Exact code path that should release seats.
5. Whether admin reads should show expired lifecycle automatically.
6. Safe options for existing smoke orders:
   - wait for existing job;
   - call existing admin endpoint if verified to release seats;
   - use a one-off ops script;
   - add a controlled admin expiry endpoint in a future prompt.
7. Risk analysis:
   - overselling risk;
   - stale holds risk;
   - manual cancellation risk;
   - open handoff on Order #53.
8. Recommendation:
   - B14F implementation/fix if needed;
   - B14G production cleanup if needed.

Update:

`docs/CHAT_HANDOFF.md`

Add concise B14E diagnostic bullet, no fix claimed.

Update:

`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Add/update item:
- expired temporary holds #52/#53 remained active after `reservation_expires_at` and Tour #6 seats stayed 7;
- B14E diagnostic identifies required fix/remediation.

Create:

`docs/HANDOFF_B14E_TEMP_HOLD_EXPIRY_RELEASE_DIAGNOSTIC_TO_NEXT_STEP.md`

Include:
- findings;
- recommended next prompt;
- whether safe cleanup endpoint exists;
- whether production orders #52/#53 can be safely cleaned now or need a fix first.

## After completion report

Return:

1. docs changed;
2. key findings;
3. whether automatic expiry exists;
4. whether safe existing cleanup endpoint exists;
5. recommended next step;
6. `git status --short`;
7. `git diff --stat`;
8. confirmation:
   - docs-only;
   - no code;
   - no tests;
   - no migrations;
   - no production API calls;
   - no production data mutation;
   - no order/payment/reservation mutation.