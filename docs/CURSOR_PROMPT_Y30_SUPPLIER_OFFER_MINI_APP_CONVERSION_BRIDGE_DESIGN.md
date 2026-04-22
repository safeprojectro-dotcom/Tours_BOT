Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- current `docs/CHAT_HANDOFF.md`
- supplier onboarding / supplier offer intake / supplier offer moderation-publication already implemented
- Telegram admin offer moderation workspace already implemented
- Telegram admin supplier moderation workspace already implemented
- current supplier offer publication already creates public Telegram channel visibility
- Layer A (`tours`, booking, payment, Mini App catalog/detail/booking flow) remains the customer-facing execution truth

Это design-only step.
Не писать runtime code.
Не менять migrations.
Не менять tests.
Не делать hidden implementation.

## Goal
Define the correct product/architecture model for:

**Supplier Offer -> Mini App Conversion Bridge**

with the accepted product rule:

- published supplier offers must remain visible in the Telegram channel as advertising/showcase content
- channel posts may continue to exist even when the offer is no longer bookable
- the Mini App must always show the current actual executable truth
- users arriving from a published supplier offer should land on an offer-aware Mini App surface
- the Mini App must decide whether the offer is:
  - bookable now
  - sold out
  - assisted only
  - no longer executable
  - or suitable only as a path into the broader catalog

## Critical design clarification
Do NOT assume:
- `publish = directly create live Layer A tour`
- `supplier_offer == tour`
- channel CTA must disappear when inventory changes
- published offer must be removed from the channel when no longer bookable

Accepted product direction:
- the Telegram channel is a discovery / advertising surface
- the Mini App/catalog/detail layer is the source of current commercial truth for customer actionability

## What this design must solve

### 1. Channel CTA contract
A published supplier offer in Telegram currently has CTA such as:
- `Detalii`
- `Rezervare`

Design the correct contract for what those CTAs should mean.

The user must not land in a dead end.
At the same time, the channel post may stay visible even if the offer later becomes sold out or otherwise non-bookable.

Define:
- whether channel CTA should always lead into a stable Mini App offer landing
- whether `Detalii` and `Rezervare` should remain separate or converge to the same offer-aware landing
- how CTA meaning changes when the offer is no longer executable

### 2. Offer-aware Mini App landing
Design a Mini App offer-aware landing surface for published supplier offers.

This surface should be able to show:
- the supplier offer itself as published/showcased content
- the current actual commercial state
- the allowed user action now

Possible outcomes when user lands:
- bookable now
- sold out / no seats
- whole-bus no longer available for self-service
- assisted only
- view-only + browse alternatives

### 3. Relationship between supplier_offers and tours
Design explicitly:
- which fields between `supplier_offers` and `tours` overlap
- which fields do not overlap
- why they are not the same object
- what kind of explicit mapping/bridge is needed

Clarify:
- `supplier_offer` is a supplier/commercial/publication object
- `tour` is a Layer A execution/catalog object
- a direct 1:1 uncontrolled merge is not acceptable

### 4. Conversion bridge model
Design the recommended bridge model between:
- `supplier_offer`
- Mini App landing
- optional executable Layer A `tour`

Important:
do not assume every published supplier offer must always become a bookable tour.

Possible states to reason about:
- published only
- published + landing available
- published + linked to executable tour
- published + sold out
- published + assisted only
- published + not currently executable but still viewable

### 5. Customer actionability vs visibility
Design the rule that:

**visibility != bookability**

The fact that an offer is still visible in the channel does not mean it is still purchasable.

Define how Mini App should determine and display:
- visible but not bookable
- visible and bookable
- visible but assisted-only
- visible but sold out

### 6. Per-seat vs full-bus policy interaction
The design must explicitly cover both:
- per-seat offers
- full-bus / whole-bus offers

Scenarios to cover:
- per-seat offer with seats available
- per-seat offer sold out
- full-bus offer with “virgin capacity” / whole vehicle available
- full-bus offer no longer available because partial sales/holds/confirmed seats exist
- offer published in channel but not self-service executable now

Do not redesign Phase 7.1 sales-mode truth.
Reuse it conceptually.

### 7. Publishing order vs conversion readiness
The user explicitly clarified this product direction:

- the offer must remain in the channel in any case as advertising/showcase content
- the Mini App should hold the current truth

Therefore, the design must NOT require:
- “do not publish until booking-ready”

Instead, define:
- published offer should have a stable Mini App entry target
- Mini App entry target can exist even before or after executable booking is available
- bookability is determined dynamically by Mini App/current policy state

### 8. Stable public entry design
Design the safest public link target from channel post.

Likely candidates:
- Mini App route keyed by `supplier_offer_id`
- stable public slug
- bridge record id

Clarify:
- what the stable entry target should be
- whether it should survive inventory changes
- how it should behave if linked executable object changes over time

### 9. Optional Layer A tour creation/linking
Design whether conversion bridge may optionally:
- create a Layer A `tour`
- link to an existing Layer A `tour`
- avoid linking entirely and stay view-only / assisted-only

Be explicit about the recommended default.

### 10. What the customer should see
Define the expected user experience for a channel visitor:

#### Case A: offer currently bookable
- sees supplier-offer landing
- sees actual availability
- gets `Rezervă` / `Cumpără` / equivalent CTA

#### Case B: sold out
- sees the same offer landing
- sees that the offer is no longer available
- gets alternative CTA such as:
  - browse catalog
  - see other offers
  - later assisted path if needed

#### Case C: full-bus not self-service executable now
- sees the offer landing
- sees that direct booking is unavailable
- can browse alternatives or request assisted path later

### 11. Boundaries to preserve
This design must preserve:
- Layer A booking/payment semantics
- RFQ/bridge/payment-entry/reconciliation semantics
- supplier profile governance separate from offer lifecycle
- offer moderation separate from supplier profile moderation
- admin does not edit supplier-authored content by default
- channel publication remains moderation-governed

### 12. Coupon / promo future hook
Discuss how offer-specific coupons should later attach to the conversion/commercial layer rather than directly to raw supplier publication text.

Do not implement it now.
Just define the design hook.

## Constraints
Do NOT:
- implement code
- redesign Layer A
- merge `supplier_offers` and `tours`
- force all published offers into bookable tours
- require channel posts to disappear when not bookable
- silently change sales-mode rules
- invent unsupported payment or waitlist behavior

## Required design output
Produce a narrow design recommendation covering:
1. stable channel CTA contract
2. Mini App offer-aware landing model
3. `supplier_offers` vs `tours` mapping principles
4. conversion bridge states / lifecycle
5. actionability rules (bookable / sold out / assisted / view-only)
6. interaction with per-seat vs full-bus policy
7. recommended implementation sequence
8. postponed items / non-goals

## Preferred files
Prefer creating:
- `docs/SUPPLIER_OFFER_MINI_APP_CONVERSION_BRIDGE_DESIGN.md`

Update continuity docs only if narrowly justified.

## Before coding
Output briefly:
1. current state
2. why this design gate is needed now
3. artifacts to inspect
4. risks if implementation starts without this design step

## After coding
Report exactly:
1. files changed
2. code changes none
3. migrations none
4. design recommendation summary
5. safest implementation sequence
6. postponed items
7. compatibility notes

## Important note
This is design-only.
Do not implement the bridge in this step.