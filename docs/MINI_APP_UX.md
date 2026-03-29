# Mini App UX

## Project
Tours_BOT

## Purpose
Define the Mini App UX before Phase 5 UI implementation so the future Flet Mini App can be built against an explicit screen map, CTA hierarchy, and user-visible state model.

This document is documentation-only. It does not add Flet UI, Mini App auth/init endpoints, booking/payment API delivery, waitlist workflow, or handoff workflow implementation.

---

## 1. Current Project State Summary

The project is currently at `Phase 4 / Step 15 completed`.

Implemented foundations already available in the codebase:
- PostgreSQL-first backend architecture
- ORM models, migrations, repositories, and Pydantic schemas
- read-oriented catalog, tour, boarding-point, user, order, and payment services
- private Telegram bot browsing and reservation-preparation flow
- temporary reservation creation with seat decrement and reservation expiry timestamp
- payment entry and idempotent payment reconciliation
- payment webhook/API delivery slice with thin route design
- reservation expiry worker with safe seat restoration
- notification preparation, dispatch, delivery, outbox, recovery, retry, and reminder groundwork

Architecture constraints already in force:
- service layer owns business rules
- repositories stay persistence-oriented
- bot and backend processes remain conceptually separate
- payment reconciliation remains the single place that confirms paid state
- reservation timer semantics come from backend logic, not UI guesses

---

## 2. Phase 4 Completed

Phase 4 completed the following slices:
- payment entry foundation via `PaymentEntryService`
- payment reconciliation via `PaymentReconciliationService`
- webhook/API payment delivery slice
- reservation expiry automation
- notification preparation and dispatch foundation
- `telegram_private` notification delivery
- payment-pending reminder groundwork, delivery, and outbox flow
- notification outbox persistence, processing, recovery, and retry execution
- predeparture reminder groundwork and outbox flow
- departure-day reminder groundwork and outbox flow
- post-trip reminder groundwork and outbox flow

What this means for Mini App UX planning now:
- reservation lifecycle states are defined enough to design timer-aware UX
- payment entry and paid confirmation states are defined enough to design payment screens
- order/payment summary behavior exists enough to shape "My Bookings"
- notification lifecycle exists, but Mini App is not yet a delivery channel

---

## 3. Exact Next Safe Step

The exact next safe step is:
- create or update `docs/MINI_APP_UX.md`

Why this is the right bridge into Phase 5:
- `docs/IMPLEMENTATION_PLAN.md` explicitly requires Mini App UX definition before full Phase 5 implementation
- the backend and service layer now provide enough stable capability to define screen structure without inventing unsupported behavior
- this reduces the risk of duplicating business rules in UI
- this makes loading, error, timer, payment, and help states explicit before implementation spreads across multiple screens
- it preserves phase order by documenting the Mini App before adding Flet UI or Mini App endpoints

---

## 4. Files In Scope

This step touches only:
- `docs/MINI_APP_UX.md`

This step must not expand:
- `app/`
- `mini_app/`
- `tests/`
- API routing
- bot flow logic
- payment workflow logic
- waitlist workflow logic
- handoff workflow logic

---

## 5. Scope Guardrails

This document must stay aligned with current implementation reality.

Use these labels throughout this UX definition:
- `Implemented foundation`: supported today by the existing backend/service layer
- `Phase 5 delivery needed`: screen behavior can be built in Phase 5 on top of existing services, but Mini App-specific UI/API delivery is not implemented yet
- `Postponed`: required by product direction, but not implemented yet and must not be presented as already supported

Current important product/technical constraints:
- Mini App is part of MVP product scope
- Mini App must be mobile-first
- booking is time-limited
- full payment confirms the order
- waitlist is required by product, but workflow implementation is still postponed in the codebase
- handoff is required by product, but Mini App handoff workflow is still postponed in the codebase
- current payment provider behavior is mock/provider-agnostic and may evolve before real Mini App payment rollout

---

## 6. UX Principles

The Mini App must be:
- mobile-first
- simple to scan
- conversion-oriented
- multilingual-ready
- explicit about the next step
- explicit about temporary reservation timing
- aligned with the current service layer
- supportive of help and human escalation entry points

The Mini App must not:
- duplicate backend business rules in UI logic
- hide payment or reservation state
- overload the user with competing primary actions
- imply that unsupported flows already exist
- silently invent waitlist or handoff behavior before those workflows are implemented

---

## 7. Main User Goals

The Mini App should eventually support these product goals:
1. browse tours
2. view tour details
3. reserve seats temporarily
4. continue to payment
5. review booking/payment state
6. adjust language or basic app preferences
7. ask for help

For the current checkpoint, goals `1-5` can be designed directly against existing Phase 2-4 foundations.

Goals not yet fully supported in the current backend implementation:
- join waitlist
- create full handoff workflow from Mini App

These remain documented as future or postponed behavior only.

---

## 8. Proposed Screen Map

Recommended Phase 5 Mini App screen map:
1. Catalog
2. Filters
3. Tour Details
4. Reservation
5. Payment
6. My Bookings
7. Booking Detail / Status View
8. Language / Settings
9. Help / Operator Entry

Additional state surfaces, not standalone primary screens:
- no-results state
- no-seats state
- reservation-expired state
- payment-pending state
- payment-confirmed state
- payment-issue state

Explicitly not a standalone implemented screen yet:
- waitlist join flow

Reason:
- product requires it eventually
- current codebase does not yet implement waitlist actions/workflow
- the UX may reference it as postponed or future, but must not pretend it exists

---

## 9. Screen-To-Capability Mapping

### 9.1 Catalog

Purpose:
- show open tours quickly
- provide low-friction entry into details or reservation

Capability status:
- `Implemented foundation`
- `Phase 5 delivery needed`

Current backend/service alignment:
- `CatalogLookupService`
- `CatalogPreparationService`
- `LanguageAwareTourReadService`

Should display:
- tour title
- cover/media placeholder strategy
- departure date
- duration
- base price and currency
- availability-oriented status label based on existing tour/order state
- sales status badge when safe to derive
- primary CTA: `View Details`
- secondary CTA: `Reserve`

Notes:
- direct `Reserve` from card is acceptable only if the UI already has enough context to enter reservation cleanly
- if card content is minimal, `View Details` should remain the dominant action
- media/gallery behavior is Phase 5 UI work, not part of this documentation step

### 9.2 Filters

Purpose:
- narrow catalog results without overwhelming the user

Capability status:
- `Implemented foundation`
- `Phase 5 delivery needed`

Current backend/service alignment:
- catalog search/filtering groundwork from `CatalogLookupService`
- language-aware tour read support

Safe initial filters for Phase 5:
- departure date or date range
- destination keyword
- budget range where one-currency filtering remains safe

Do not assume as already supported unless added later:
- complex category system
- advanced duration segmentation
- recommendation logic
- marketing/source-aware personalization

Primary CTA:
- `Apply Filters`

Secondary CTA:
- `Reset`
- `Back to Catalog`

### 9.3 Tour Details

Purpose:
- support decision-making before reservation

Capability status:
- `Implemented foundation`
- `Phase 5 delivery needed`

Current backend/service alignment:
- `TourDetailService`
- `LanguageAwareTourReadService`
- `BoardingPointService`

Should display when available from current data model:
- title
- short and full description
- program text
- included text
- excluded text
- departure and return datetime
- price and currency
- available seats summary when safe
- boarding points
- payment/cancellation policy summary sourced from current documented rules
- primary CTA: `Reserve`
- secondary CTA: `Back to Catalog`
- support CTA: `Need Help`

Do not imply as already implemented:
- rich gallery behavior beyond available media assumptions
- dynamic recommendation carousel
- live operator conversation

### 9.4 Reservation

Purpose:
- convert a selected tour into a temporary reservation

Capability status:
- `Implemented foundation`
- `Phase 5 delivery needed`

Current backend/service alignment:
- `TemporaryReservationService`
- `BoardingPointService`
- existing reservation expiry policy from service layer

Should allow:
- choose seat count
- choose boarding point
- review selected tour summary
- see total amount summary
- confirm reservation

Must show clearly:
- reservation is temporary
- reservation expiry timestamp
- what happens after expiry
- that seat availability is affected by reservation creation

Primary CTA:
- `Confirm Reservation`

Secondary CTA:
- `Back`

Support CTA:
- `Need Help`

Postponed behavior on this screen:
- waitlist join if no seats remain
- custom pickup escalation flow
- group-booking handoff workflow

These may be referenced as future support paths but must not be treated as already implemented.

### 9.5 Payment

Purpose:
- guide the user from active reservation to payment initiation

Capability status:
- `Implemented foundation`
- `Phase 5 delivery needed`

Current backend/service alignment:
- `PaymentEntryService`
- `PaymentReadService`
- `PaymentSummaryService`
- `PaymentReconciliationService`

Should display:
- reservation reference
- payment session/reference when created
- amount due
- payment status summary
- reservation expiry timestamp
- primary CTA: `Pay Now`
- secondary CTA: `Back to Booking`
- support CTA: `Payment Help`

Important UX constraints:
- do not claim payment success until backend-confirmed state is available
- payment success/failure/pending messages must reflect real state only
- current provider flow is mock/provider-agnostic, so UX copy should remain provider-neutral at this stage

### 9.6 My Bookings

Purpose:
- show the user's reservation and order state in one place

Capability status:
- `Implemented foundation`
- `Phase 5 delivery needed`

Current backend/service alignment:
- `OrderReadService`
- `OrderSummaryService`
- `PaymentSummaryService`

Should display at minimum:
- active temporary reservations
- confirmed paid bookings
- expired/unpaid items as understandable historical states
- payment status
- reservation expiry when relevant
- primary CTA per item: `Open`
- secondary CTA per item: context-dependent `Pay Now` when still valid
- support CTA: `Need Help`

Important state note:
- current expiry semantics keep `booking_status=reserved` and mark `cancellation_status=cancelled_no_payment`
- the Mini App must present this as an expired or canceled-for-no-payment user-facing state
- the UI must not expose raw status combinations without translation into human-readable meaning

Explicitly postponed in this screen:
- real waitlist entries
- operator assignment/handoff state

### 9.7 Booking Detail / Status View

Purpose:
- give one booking-level explanation screen after a user opens an item from `My Bookings`

Capability status:
- `Implemented foundation`
- `Phase 5 delivery needed`

Current backend/service alignment:
- `OrderReadService`
- `OrderSummaryService`
- `PaymentSummaryService`

Should display:
- tour summary
- seats count
- boarding point
- total amount
- booking status summary
- payment status summary
- reservation timer when still active
- last meaningful notification/next step summary where useful

Primary CTA varies by state:
- `Pay Now` if reservation is active and unpaid
- `Back to Bookings` if payment is complete
- `Browse Tours` if reservation has expired

Support CTA:
- `Need Help`

### 9.8 Language / Settings

Purpose:
- allow language selection and simple UX preferences without derailing booking flow

Capability status:
- `Implemented foundation`
- `Phase 5 delivery needed`

Current backend/service alignment:
- `UserProfileService`
- current user language persistence model

Must support:
- change language
- persist selected language
- return to previous context

Do not expand yet into:
- notification preference management
- profile editing beyond safe minimal fields
- account-management complexity

### 9.9 Help / Operator Entry

Purpose:
- provide a clear support path from Mini App without overstating current automation

Capability status:
- `Postponed` for real handoff workflow
- `Phase 5 UX definition allowed`

Current backend/service alignment:
- knowledge/help copy can draw from `KnowledgeBaseLookupService`
- real handoff lifecycle is not yet implemented

This screen may define:
- help categories
- "when to contact support" guidance
- simple explanation of supported issues
- entry CTA placeholder for future operator flow

Primary CTA:
- `Get Help`

Secondary CTA:
- `Back`

Strict rule:
- if a real handoff creation path does not exist yet, the UX must frame this as a planned support entry point, not as a live operator handoff guarantee

---

## 10. CTA Hierarchy

### 10.1 Global Hierarchy

Primary CTA categories:
- `View Details`
- `Confirm Reservation`
- `Pay Now`
- `Open Booking`

Secondary CTA categories:
- `Back to Catalog`
- `Reset Filters`
- `Back to Booking`
- `Browse Tours`

Support CTA categories:
- `Need Help`
- `Change Language`
- `Payment Help`

Future CTA categories, explicitly postponed:
- `Join Waitlist`
- `Talk to Operator`

### 10.2 Hierarchy Rules

Rules that must govern every screen:
- each screen gets exactly one dominant primary CTA
- support CTA must remain visible but visually secondary
- destructive or unavailable actions must not compete with the main next step
- if the user's next action is payment, `Pay Now` must dominate
- if the user does not yet have enough context to reserve safely, `View Details` must dominate over `Reserve`
- postponed actions may be shown only as disabled, absent, or explicitly "coming later" documentation notes, not as implied live functionality

### 10.3 Recommended Primary CTA By Screen

- Catalog: `View Details`
- Filters: `Apply Filters`
- Tour Details: `Reserve`
- Reservation: `Confirm Reservation`
- Payment: `Pay Now`
- My Bookings: `Open`
- Booking Detail / Status View:
- `Pay Now` when active and unpaid
- `Browse Tours` when expired
- `Back to Bookings` when already complete
- Language / Settings: `Save Language`
- Help / Operator Entry: `Get Help`

---

## 11. Loading States

Explicit loading states are required for:
- catalog load
- filtered catalog refresh
- tour detail load
- boarding-point load
- reservation creation
- payment session creation or reuse
- booking list retrieval
- booking detail retrieval
- language update
- help content load

Loading-state rules:
- always indicate that work is in progress
- disable duplicate-submit actions during reservation and payment initiation
- keep copy short and action-specific
- do not use generic indefinite spinners when a meaningful loading label can be shown

Suggested loading copy patterns:
- `Loading tours...`
- `Loading tour details...`
- `Creating reservation...`
- `Preparing payment...`
- `Loading your bookings...`
- `Saving language...`

Explicitly not needed yet because workflow is postponed:
- waitlist submission loading
- real handoff submission loading

---

## 12. Empty States

### 12.1 Catalog Empty

When no tours match current filters:
- explain that no matching tours were found
- provide `Reset Filters`
- provide `Browse All Tours`
- optionally provide `Need Help`

### 12.2 My Bookings Empty

When the user has no reservations or bookings:
- explain that there are no bookings yet
- provide `Browse Tours`

### 12.3 Booking History Empty After Expiry-Only Cases

If the product later chooses to hide expired rows from the default view:
- explain that there are no active bookings
- provide `Browse Tours`

Explicitly postponed:
- no waitlist-items empty state, because waitlist workflow is not implemented yet

---

## 13. Error States

Error states must be explicit for:
- failed catalog load
- failed tour detail load
- reservation creation failure
- payment initiation failure
- booking retrieval failure
- language update failure
- generic Mini App support/help content failure

Error-state rules:
- explain in plain language
- do not expose raw technical details
- give one clear recovery path
- provide `Need Help` where recovery is not obvious

Recommended recovery patterns:
- retry current action
- go back one step
- return to catalog
- open help entry point

Explicitly postponed:
- waitlist failure state
- real handoff submission failure state

---

## 14. Reservation Timer UX

The reservation timer is a critical UX element because temporary reservation already exists in the backend.

Timer data source rules:
- timer values must come from backend reservation data
- the UI must not calculate business-policy timing on its own
- the UI may render countdown behavior, but the authoritative expiry value remains backend-owned

Timer must communicate:
- seats are held temporarily
- exact or near-exact expiry time
- expiration consequence: unpaid reservation ends and seats return to availability
- next action: payment before expiry

Timer visibility rules:
- visible on Reservation after successful reservation creation
- visible on Payment while reservation remains active
- visible in My Bookings and Booking Detail when relevant
- removed or replaced with an expired-state message when no longer active

Timer state variants:
- `active`: timer visible, payment CTA prominent
- `expiring_soon`: stronger urgency styling, same factual copy only
- `expired`: timer replaced with status message and recovery CTA

No fake urgency:
- the UI may highlight real urgency only when derived from actual remaining time
- no fabricated "last chance" messaging

---

## 15. User-Visible Booking And Payment State Model

The Mini App should translate backend state into user-friendly language.

### 15.1 Core User-Visible States

- `browsing`
- `viewing_details`
- `reservation_in_progress`
- `reservation_active_unpaid`
- `reservation_expiring_soon`
- `payment_pending`
- `payment_confirmed`
- `reservation_expired`
- `booking_confirmed`
- `help_entry_available`

### 15.2 State Translation Rules

Examples of how backend behavior should be represented:
- active reservation:
  - show as `Reserved temporarily`
  - show timer and `Pay Now`
- paid confirmed booking:
  - show as `Booking confirmed`
  - remove payment CTA
- expired unpaid reservation:
  - show as `Reservation expired`
  - do not show raw enum combination
  - offer `Browse Tours` and, if still possible later, future recovery options

### 15.3 States Not Yet Supported As Real Mini App Workflow

These may appear in future product scope but are not yet active workflow states for Mini App:
- `waitlist_joined`
- `operator_assigned`
- `handoff_in_progress`

---

## 16. Help And Handoff Entry Points

Help entry should be available from:
- Tour Details
- Reservation
- Payment
- My Bookings
- Booking Detail / Status View
- major error states

Help CTA should become more prominent when:
- payment cannot be initiated
- payment state seems unclear to the user
- user has no suitable tour result
- reservation has expired and the user needs next-step guidance
- user wants custom pickup, group booking, discount, complaint handling, or a human directly

Current implementation boundary:
- help guidance can be designed now
- real handoff workflow remains postponed

Therefore, UX copy must distinguish between:
- `Help information available now`
- `Operator/human path planned but not yet implemented in Mini App`

The Mini App must not promise:
- that an operator has been contacted
- that a handoff record was created
- that the user is already in a human queue

unless Phase 7 implementation later makes those statements true.

---

## 17. Multilingual UX Rules

The Mini App must:
- render in the user's selected or persisted language
- use existing language persistence rules
- follow explicit fallback behavior when translation is missing
- avoid mixed-language confusion on the same screen

Current technical alignment:
- language persistence already exists in the current architecture
- language normalization is currently short-code based
- translation fallback must remain explicit

UX fallback rules:
- if a translated field exists, use it
- if a translated field is missing, use the defined fallback language consistently for that field group
- if a fallback is displayed, keep CTA labels and critical booking/payment instructions readable and consistent

Do not do:
- partial mixed-language blocks when a cleaner fallback is possible
- silent language switching that changes the whole app unpredictably

---

## 18. Explicitly Postponed Before UI Implementation

The following items remain outside this step and must not be implemented or implied as live:
- Flet Mini App implementation
- Mini App auth/init endpoints
- Mini App API delivery changes
- Mini App-specific booking endpoint additions
- Mini App-specific payment endpoint additions
- waitlist workflow implementation
- handoff workflow implementation
- group delivery
- content/admin expansions unrelated to Mini App UX

Within the UX itself, these should be marked as postponed or future:
- waitlist join action
- alternative-tour automation beyond simple browse/filter return paths
- real operator request submission
- operator assignment/status visibility
- provider-specific payment UX
- rich notification preferences

---

## 19. Remaining Postponed Work Beyond This Step

The broader roadmap items still postponed after this UX-definition step include:
- full Phase 5 Mini App UI implementation
- Phase 6 admin panel work
- Phase 7 group assistant and operator handoff lifecycle
- waitlist actions/workflow
- broader scheduler/orchestration
- refund workflow
- Mini App as a notification channel
- content publication workflows

This document must not pull those items forward.

---

## 20. Manual Validation Checklist For Future Phase 5 Work

When Phase 5 UI implementation begins, validate at minimum:
- catalog is readable on mobile
- filters do not overwhelm the user
- tour details support decision-making clearly
- reservation form explains temporary hold correctly
- timer remains visible and understandable
- payment screen stays provider-neutral until real provider specifics are introduced
- booking list translates raw backend states into understandable user statuses
- help entry is visible on high-friction screens
- missing translations fall back gracefully
- error states always provide a next action
- postponed actions are not accidentally presented as live functionality

---

## 21. Implementation Guidance For Phase 5

When Phase 5 starts, implementation should follow this order:
1. Catalog and Filters
2. Tour Details
3. Reservation
4. Payment
5. My Bookings and Booking Detail
6. Language / Settings
7. Help / Operator Entry placeholder aligned with postponed handoff reality

General build rule:
- reuse the existing service layer
- keep business rules out of UI code
- keep timer, payment, and booking state backend-owned
- add thin Mini App delivery/API surfaces only after the UX contract above is accepted
