# CURSOR_PROMPT_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT

Implement a narrow, safe fix for the boarding-points / reservation-preparation mismatch discovered in B14A.

## Context

B13G full conversion smoke passed for:

- Supplier Offer #12
- Tour #6
- tour_code = `B10-SO12-04fb1f`
- execution link #5 active
- publish audit persisted
- conversion_status_panel:
  - showcase.status = `published`
  - tour_bridge.status = `linked`
  - catalog.status = `listed_for_sale`
  - booking_link.status = `active`
  - customer_action.status = `open_exact_mini_app_tour`

B14A diagnostic found:

- Telegram showcase CTA currently uses stable supplier-offer landing `/supplier-offers/{id}` by design.
- Reservation preparation blocker is separate.
- Mini App route `GET /mini-app/tours/{tour_code}/preparation` returns:
  - `tour is not available for reservation preparation`
- Source:
  - `app/api/routes/mini_app.py`
  - `MiniAppReservationPreparationService.get_preparation(...)`
  - `PrivateReservationPreparationService.get_preparable_tour(...)`
- For `per_seat` tours, no boarding points ⇒ not preparable.
- Tour detail/catalog can still show the tour, but reservation preparation is stricter.
- Supplier Offer #12 had `boarding_places_text` / boarding data, but bridged Tour #6 appears to have no materialized boarding points.

## Goal

Fix the source of the mismatch for future bridge-created tours:

When a Supplier Offer with boarding/place text is materialized into a new Tour via the Supplier Offer → Tour bridge, the created Tour should receive boarding point rows compatible with `PrivateReservationPreparationService.get_preparable_tour`.

This should allow future per-seat bridged tours to pass reservation preparation when the supplier offer has usable boarding data.

## Scope

Allowed:
- app code changes in bridge/materialization services;
- repositories/helpers if needed;
- unit tests;
- documentation updates;
- no production calls.

Prefer a minimal implementation.

## Required inspection

Read:
- `docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/MINI_APP_UX.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`

Inspect code:
- Supplier Offer → Tour bridge/materialization service
- Tour model and boarding point model
- Tour repository / admin tour write service
- `PrivateReservationPreparationService.get_preparable_tour`
- `MiniAppReservationPreparationService.get_preparation`
- tests around:
  - supplier offer tour bridge
  - mini app reservation preparation
  - admin review package / conversion panel

Search for:
- `boarding_places_text`
- `TourBoarding`
- `boarding_points`
- `get_preparable_tour`
- `tour is not available for reservation preparation`
- `create_tour_bridge`
- `SupplierOfferTourBridge`

## Implementation requirements

### 1. Do not mutate existing production data

Do not add data migrations that modify Tour #6 or any production rows.

This code change should fix future materializations.

Existing production Tour #6 may still need an explicit ops/data remediation step after deployment.

### 2. Bridge-created tours should materialize boarding points

When bridge creates a new Tour from a Supplier Offer:

- If the Supplier Offer has usable boarding text, create at least one boarding point for the new Tour.
- Use existing Tour boarding point model/repository conventions.
- Do not invent complex geolocation.
- Minimal acceptable mapping:
  - label/name from supplier offer boarding text;
  - keep ordering stable;
  - use nullable fields where model allows;
  - no fake coordinates.
- If supplier boarding text contains multiple places, use the existing project convention if one exists.
  - If there is no convention, implement the safest minimal split:
    - preserve full text as one boarding point label, unless current code already has a splitter.
- Do not create duplicate boarding points on idempotent bridge replay.
- If bridge links an existing Tour rather than creating a new Tour, do not silently mutate that existing Tour unless existing behavior already does so.

### 3. Preserve Layer A boundaries

Do not:
- create orders;
- create reservations;
- create payments;
- call payment services;
- change TemporaryReservationService;
- weaken reservation preparation guards.

The fix is to provide required Tour data, not to bypass reservation readiness.

### 4. Tests

Add or update unit tests to prove:

1. Supplier Offer with `boarding_places_text` creates a bridged Tour with boarding point(s).
2. The bridge replay does not duplicate boarding points.
3. The created per-seat Tour becomes preparable according to the same condition used by `PrivateReservationPreparationService.get_preparable_tour`, if the rest of required fields are present.
4. Existing publish / audit / execution link tests are not affected.
5. If Supplier Offer has no boarding text, behavior remains safe and preparation can still be blocked.

Use existing test style and fixtures.

Run a focused test set, for example:
- relevant supplier offer bridge tests;
- relevant mini app reservation preparation tests;
- relevant review package / conversion panel tests.

If exact test names differ, choose the closest existing tests and report them.

### 5. Documentation

Update:
- `docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md`
  - Add B14C implementation note / follow-up result.
- `docs/CHAT_HANDOFF.md`
  - Add concise B14C bullet.
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
  - Update the Tour #6 follow-up:
    - future bridge-created tours are fixed;
    - existing Tour #6 may still need manual data remediation unless a separate safe ops step is performed.

Create:
- `docs/HANDOFF_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT_TO_NEXT_STEP.md`

The handoff must include:
- changed files;
- what was fixed;
- what was not fixed;
- tests run;
- production note:
  - no production data was changed;
  - existing Tour #6 may still need boarding point remediation after deploy;
- next recommended step:
  - B14D production-safe remediation/check for Tour #6, or
  - B14D Mini App reservation smoke after data is corrected.

## Forbidden

Do not:
- call production APIs;
- edit production data;
- publish/retry/resend;
- create or close execution links;
- create orders;
- create reservations;
- create payments;
- add payment logic;
- weaken reservation guards;
- change channel CTA behavior in this prompt;
- add migrations that mutate existing production rows.

## After completion report

Return:

1. brief pre-code summary of the root cause;
2. files changed;
3. implementation summary;
4. tests added/changed;
5. tests run and results;
6. production note for Tour #6 existing data;
7. next recommended prompt name;
8. `git status --short`;
9. `git diff --stat`;
10. confirmations:
   - no production API calls;
   - no publish/retry/resend;
   - no execution-link mutation;
   - no orders/payments/reservations;
   - no CTA behavior change;
   - no weakening of reservation guards.