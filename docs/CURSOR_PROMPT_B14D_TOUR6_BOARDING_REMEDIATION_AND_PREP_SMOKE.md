# CURSOR_PROMPT_B14D_TOUR6_BOARDING_REMEDIATION_AND_PREP_SMOKE

Prepare a production-safe remediation and smoke runbook for existing Tour #6 / `B10-SO12-04fb1f`.

This is docs / ops guidance first. Do not mutate production from Cursor.

## Context

B13G full conversion smoke passed for:

- Supplier Offer #12
- Tour #6
- tour_code = `B10-SO12-04fb1f`
- execution link #5 active
- publish audit persisted
- Mini App supplier-offer landing shows `Bookable now`
- conversion_status_panel:
  - showcase.status = `published`
  - tour_bridge.status = `linked`
  - catalog.status = `listed_for_sale`
  - booking_link.status = `active`
  - customer_action.status = `open_exact_mini_app_tour`

B14A diagnosed the remaining issue:

- Mini App exact tour opens.
- Catalog and landing look bookable.
- But reservation preparation shows:
  - `tour is not available for reservation preparation`
- Root cause: for per-seat tours, `PrivateReservationPreparationService.get_preparable_tour` requires boarding point rows.
- Existing Tour #6 was created before B14C, so it may lack boarding points.

B14C implemented future fix:

- Supplier Offer → Tour bridge now materializes boarding points for future new bridge-created tours.
- No production data was changed.
- Existing Tour #6 still requires safe ops remediation if boarding points are missing.

## Goal

Create a safe runbook to:

1. Read-only verify whether Tour #6 has boarding points.
2. Identify the safest existing admin/API/data path to add one boarding point to Tour #6 if missing.
3. Verify `GET /mini-app/tours/B10-SO12-04fb1f/preparation` after remediation.
4. Verify Mini App `Rezerva locuri` flow no longer shows `tour is not available for reservation preparation`.
5. Record results.

## Required inspection

Read:
- `docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md`
- `docs/HANDOFF_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT_TO_NEXT_STEP.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/MINI_APP_UX.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`

Inspect code:
- Tour / boarding point ORM models.
- Repositories for boarding points.
- Admin routes for tours and boarding points.
- Mini App route:
  - `GET /mini-app/tours/{tour_code}/preparation`
- `PrivateReservationPreparationService.get_preparable_tour`
- `MiniAppReservationPreparationService.get_preparation`

Search:
- `boarding_points`
- `TourBoarding`
- `BoardingPoint`
- `boarding`
- `/admin/tours`
- `preparation`
- `tour is not available for reservation preparation`

## Deliverable

Create:

`docs/B14D_TOUR6_BOARDING_REMEDIATION_AND_PREP_SMOKE_RUNBOOK.md`

The runbook must include:

### 1. Safety

- Production ops only.
- No publish/retry/resend.
- No execution-link mutation.
- No order/payment mutation.
- Do not create a real reservation unless explicitly approved.
- Use read-only checks first.
- If write is needed, add only a boarding point for Tour #6.

### 2. Current known IDs

- supplier_offer_id = 12
- tour_id = 6
- tour_code = `B10-SO12-04fb1f`
- execution_link_id = 5

### 3. Read-only checks

Provide PowerShell commands to check:

- healthz;
- review-package state for Offer #12;
- linked_tour_catalog;
- execution_links_review;
- conversion_status_panel;
- exact Mini App preparation endpoint for Tour #6;
- available admin route/schema for Tour #6 boarding points, if any exists.

### 4. Boarding remediation options

Document the safest option based on code inspection:

Option A:
- Existing admin API supports adding/updating boarding point rows for a tour.
- Provide exact command body and endpoint.

Option B:
- No admin endpoint exists.
- Provide Railway shell SQL/psql-safe remediation only if it matches existing table/model constraints.
- Prefer a minimal row:
  - tour_id = 6
  - place/city/label = `Timisiara` or exact source from Offer #12
  - departure time consistent with Tour #6
  - no fake coordinates
  - notes: `B14D remediation for Offer #12 smoke`

Option C:
- If no safe write path can be identified, stop and recommend a small admin endpoint / script prompt instead.

### 5. Post-remediation smoke

Provide commands to check:

- boarding points now exist;
- `/mini-app/tours/B10-SO12-04fb1f/preparation` no longer returns the 404 detail;
- Mini App `Rezerva locuri` opens preparation screen;
- do not confirm reservation unless explicitly approved.

### 6. Result recording template

Add a template for recording:
- timestamp;
- operator;
- action taken;
- before/after;
- endpoint used;
- whether preparation opened;
- whether reservation was created: should be `no` unless explicitly approved.

Update:

`docs/CHAT_HANDOFF.md`

Add a concise B14D runbook bullet, no claim that remediation has been executed.

Update:

`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Keep or refine Tour #6 follow-up:
- B14C future fix done.
- B14D runbook prepared.
- Existing Tour #6 still needs operator-run remediation/smoke until executed.

Create:

`docs/HANDOFF_B14D_TOUR6_BOARDING_REMEDIATION_AND_PREP_SMOKE_TO_NEXT_STEP.md`

Include:
- what B14D runbook covers;
- safety boundaries;
- whether code inspection found admin API or SQL path;
- exact next operator action;
- reminder to rotate ADMIN_API_TOKEN if not yet done.

## Forbidden

Do not:
- edit app code;
- edit tests;
- add migrations;
- call production APIs;
- publish;
- retry/resend;
- create/close/replace execution links;
- create orders;
- create reservations;
- create payments;
- mutate production data from Cursor.

## After completion report

Return:

1. docs changed;
2. whether a safe existing admin/API boarding remediation path exists;
3. if not, what path is recommended;
4. key read-only commands from the runbook;
5. `git status --short`;
6. `git diff --stat`;
7. confirmation:
   - docs-only;
   - no code;
   - no tests;
   - no migrations;
   - no API calls;
   - no production data mutation;
   - no publish/retry/resend;
   - no execution-link mutation;
   - no orders/payments/reservations.