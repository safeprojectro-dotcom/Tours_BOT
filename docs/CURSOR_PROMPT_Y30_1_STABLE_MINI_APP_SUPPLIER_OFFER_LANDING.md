Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y30 design accepted
- `docs/SUPPLIER_OFFER_MINI_APP_CONVERSION_BRIDGE_DESIGN.md`
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не сливать `supplier_offers` и `tours`.
Не реализовывать full conversion bridge в этом шаге.

## Goal
Implement the first narrow runtime slice of the Supplier Offer -> Mini App Conversion Bridge:

**stable Mini App landing for published supplier offers (read-only first)**

This step must remove the dead-end problem for users arriving from channel CTA, but it must remain narrow:
- stable landing exists
- offer context is visible
- user can continue into broader catalog if needed
- no full bookability resolver yet
- no direct booking activation yet unless already trivially supported by current truth

## Accepted design truth
- Published supplier offers remain visible in Telegram channel as showcase/advertising content.
- Channel CTA must lead to a stable Mini App offer-aware landing.
- Mini App landing must be able to exist even if the offer is not currently executable/bookable.
- Visibility != bookability.
- `supplier_offer` remains separate from Layer A `tour`.

## Exact scope

### 1. Stable Mini App route
Add a stable Mini App route/entry for published supplier offers.

Recommended shape:
- route keyed by `supplier_offer_id`
or another stable supplier-offer identity

The route must remain stable even if the executable booking linkage is absent or later changes.

### 2. Read-only supplier-offer landing API/service
Add the narrowest backend/API/service support needed so Mini App can load a published supplier offer landing.

Landing must show:
- supplier offer title
- supplier offer description / commercial summary
- departure / return info
- price / currency if available
- current publication presence/context where useful
- enough context so the user understands what offer they opened

This is not yet full booking execution.

### 3. Published-only access rule
Landing should work only for offers that are appropriate for public landing visibility.
At minimum, keep it narrow and safe around published supplier offers.

Do not broaden into draft/ready_for_moderation/supplier-private visibility unless trivial and clearly safe.

### 4. Mini App UI surface
Add a read-only Mini App landing screen for supplier offers.

Must provide:
- visible offer context
- clear state that this is the opened offer
- clear CTA back to/browse catalog
- no dead end

### 5. Channel CTA target readiness
Prepare the system so channel CTA can safely target this stable landing.
If the existing post builder still uses older CTA targets, keep changes narrow and safe.
Do not force full CTA/publish pipeline redesign in this step unless very small and directly required.

### 6. No full actionability resolver yet
Do NOT implement the full state machine for:
- sold out
- assisted only
- full-bus unavailable
- linked executable tour
- coupon logic

Only add the narrowest placeholder/read-side basis needed for later steps.

### 7. Safe fallback UX
If the offer is visible but not directly executable yet, user must still get:
- a readable landing
- a clear next step such as:
  - browse catalog
  - return to offers
  - go back

No dead end, no broken CTA.

## What this step must NOT do
Do NOT:
- implement full conversion bridge state machine
- auto-create Layer A tours
- auto-link supplier offers to tours
- add direct booking/payment activation logic
- redesign channel publication flow broadly
- add coupons
- add supplier-offer auto retract/block policy
- redesign Layer A catalog semantics

## Likely files
Likely:
- new backend read service for published supplier offer landing
- maybe new mini-app API route
- mini_app client/UI screen additions
- maybe bot/Mini App deep-link helper glue
- focused tests for route/service/UI glue

Avoid unrelated subsystems.

## Before coding
Output briefly:
1. current state
2. why Y30.1 is the next safe step
3. likely files to change
4. risks
5. what remains postponed

## Required tests
Add/update focused tests for:
1. published supplier offer landing can be loaded
2. unpublished/non-visible offer is rejected safely
3. landing returns stable offer context fields
4. Mini App surface does not dead-end and exposes catalog fallback
5. no Layer A booking/payment semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what user can now do from channel/Mini App
6. what remains postponed
7. compatibility notes

## Important note
This is only the first bridge slice:
stable read-only Mini App landing for published supplier offers.
Do not silently expand into executable booking logic in this step.