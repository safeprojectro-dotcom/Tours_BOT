Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y30 design accepted
- Y30.1 implemented and synced in handoff
- stable Mini App landing for published supplier offers already exists
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не сливать `supplier_offers` и `tours`.
Не реализовывать direct booking/payment activation from supplier-offer landing in this step.

## Goal
Implement the next narrow read-side slice of the Supplier Offer -> Mini App Conversion Bridge:

**supplier-offer actionability resolver**

The Mini App supplier-offer landing must now show the current actionable state of the offer for the customer, without yet executing booking from that landing.

## Accepted design truth
- Published supplier offers remain visible in Telegram channel as advertising/showcase content.
- Stable Mini App landing already exists for published supplier offers.
- Visibility != bookability.
- Mini App must show current actual actionability truth for the offer.
- `supplier_offer` remains separate from Layer A `tour`.

## Exact scope

### 1. Actionability resolver
Add a narrow resolver that determines the current customer-facing state for a published supplier offer landing.

At minimum support these states:
- `bookable`
- `sold_out`
- `assisted_only`
- `view_only`

### 2. Resolver inputs
Resolver may use:
- current supplier offer data
- current linked executable object if one exists
- current inventory/sales-mode truth where already safely available
- existing sales mode policy concepts

Do not invent unsupported booking math.
Do not overreach into new execution semantics.

### 3. Per-seat logic
For per-seat offers:
- if clearly executable and seats are available -> `bookable`
- if clearly no seats remain -> `sold_out`
- otherwise fall back safely to `view_only` if execution truth is insufficient

### 4. Full-bus logic
For full-bus / whole-bus offers:
- if self-service whole-bus execution is currently allowed by existing policy truth -> `bookable`
- if not self-service executable but still visible -> `assisted_only` or `view_only`
- if clearly unavailable -> safe non-bookable state

Do not redesign sales-mode policy.
Reuse the existing conceptual policy truth.

### 5. Mini App landing UI
Update the supplier-offer landing UI to render current actionability state.

Expected behavior:
- `bookable` -> show booking-oriented CTA placeholder/path for later steps, but do not yet implement full booking execution from this landing
- `sold_out` -> show unavailable message and catalog fallback
- `assisted_only` -> show non-self-service message and catalog/help fallback
- `view_only` -> show read-only state and catalog fallback

### 6. API/read schema
Expose the actionability state in the narrowest safe backend/API shape needed by Mini App.

### 7. Safe fallback rule
If the system cannot safely prove the offer is executable/bookable right now, do NOT claim bookability.
Prefer `view_only` or `assisted_only` over false-positive booking availability.

## What this step must NOT do
Do NOT:
- trigger direct booking/payment from supplier-offer landing
- auto-create Layer A tours
- auto-link supplier offers to tours
- redesign channel publication flow
- implement coupon logic
- redesign waitlist
- redesign Layer A / RFQ / payment semantics

## Likely files
Likely:
- `app/services/mini_app_supplier_offer_landing.py`
- maybe a new small resolver/helper service
- `app/schemas/mini_app.py`
- `app/api/routes/mini_app.py`
- `mini_app/api_client.py`
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- focused tests

Avoid unrelated subsystems.

## Before coding
Output briefly:
1. current state
2. why Y30.2 is the next safe step
3. likely files to change
4. risks
5. what remains postponed

## Required tests
Add/update focused tests for:
1. published supplier offer with safe executable truth resolves to `bookable`
2. published supplier offer with no remaining availability resolves to `sold_out`
3. full-bus non-self-service case resolves to `assisted_only` or `view_only` safely
4. insufficient truth falls back safely without claiming bookability
5. existing stable landing still works
6. no Layer A booking/payment semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what the customer now sees on supplier-offer landing
6. what remains postponed
7. compatibility notes

## Important note
This is only the actionability resolver layer.
Do not silently implement direct booking/payment execution from supplier-offer landing in this step.