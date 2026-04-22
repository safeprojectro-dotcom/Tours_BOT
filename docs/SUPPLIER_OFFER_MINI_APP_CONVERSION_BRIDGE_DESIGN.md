# Supplier Offer -> Mini App Conversion Bridge Design (Y30)

## Status
- Design-only gate.
- No runtime implementation in this step.
- No migration changes in this step.
- No test changes in this step.

## Purpose
Define a stable conversion model from published supplier showcase posts in Telegram channel to Mini App customer actionability, while preserving accepted truth:
- channel visibility is a discovery/advertising surface;
- Layer A + Mini App policy is the execution and commercial action truth;
- visibility does not imply current bookability.

---

## 1) Guardrails (Must Stay True)

- Do not redesign Layer A booking/payment semantics.
- Do not redesign RFQ/bridge/payment-entry/reconciliation semantics.
- Do not merge supplier profile moderation with supplier offer moderation.
- Do not merge `supplier_offers` with `tours`.
- Do not require channel post removal when offer becomes non-bookable.
- Do not force `publish => create live Layer A tour`.
- Do not silently change Phase 7.1 sales-mode truth.

---

## 2) Channel CTA Contract

## Problem
Current published offer posts can remain in channel over time while execution state changes. CTA must never lead to dead end.

## Decision
Channel CTA must always lead to a **stable Mini App offer-aware landing** keyed by supplier offer identity.

## Recommended CTA semantics
- `Detalii`: open supplier-offer landing in Mini App (read + actionability state).
- `Rezervare`: open the same landing (optionally with "intent=book" hint), not a direct hard jump to booking execution.

Rationale:
- one stable entry contract is safer than bifurcated routes;
- landing can always re-evaluate current executable truth dynamically;
- avoids stale deep links directly into deprecated execution paths.

## Behavioral rule
CTA meaning is stable ("open this showcased offer in Mini App"), while available actions on landing are dynamic.

---

## 3) Offer-Aware Mini App Landing Model

## New read-side concept
`SupplierOfferLanding` (presentation/read model) resolved by stable public key from channel post.

## Landing must show
- showcased supplier offer content (title/description/schedule/media context);
- publication context (still visible/archived messaging if needed later);
- current actionability state (derived at request time);
- explicit next action CTA.

## Required outcomes
- `bookable_now`
- `sold_out`
- `assisted_only`
- `not_currently_executable`
- `browse_alternatives`

## Customer UX principle
User always lands on meaningful page:
- never "not found" for still-valid showcase identity;
- no silent failure if executable path is currently unavailable.

---

## 4) `supplier_offers` vs `tours` Mapping Principles

## They are different objects
`supplier_offer`:
- supplier-authored commercial/showcase entity;
- moderation/publication lifecycle;
- channel discovery surface identity.

`tour`:
- Layer A executable catalog/booking/payment entity;
- operational inventory + reservation/payment policy truth.

## Overlap (non-authoritative by itself)
- title/route-like text;
- dates/timing;
- sales mode intent fields;
- pricing hints.

## Non-overlap
- `supplier_offer`: moderation/publication state, showcase metadata, supplier narrative.
- `tour`: authoritative seat availability, reservation and payment execution semantics.

## Mapping requirement
Use explicit bridge/mapping contract; no uncontrolled implicit 1:1 merge.

---

## 5) Conversion Bridge Model (Recommended)

## Core model
Published supplier offer always has stable landing identity.
Executable Layer A link is optional and dynamic.

## Recommended bridge states (read/policy-level)
1. `published_only`
   - channel visible, landing visible;
   - no executable Layer A path currently active.
2. `published_landing_available`
   - same as above, explicitly resolved for customer.
3. `published_linked_executable`
   - landing resolves active executable Layer A tour context.
4. `published_sold_out`
   - linked executable exists but not currently bookable.
5. `published_assisted_only`
   - policy says no self-service now (e.g. full-bus no longer virgin).
6. `published_not_currently_executable`
   - no valid self-service execution now; landing remains usable.

## Important
All states keep channel discovery visibility contract intact.

---

## 6) Actionability Rules (Visibility != Bookability)

Landing resolver determines one customer-facing actionability state per request:

- `visible_and_bookable`
  - show reserve/buy CTA.
- `visible_and_sold_out`
  - show sold-out explanation + alternative browse CTA.
- `visible_assisted_only`
  - show assisted-only explanation + assisted route hook (future) and browse CTA.
- `visible_view_only`
  - show non-executable explanation + browse alternatives.

No state should imply post deletion is required.

---

## 7) Per-Seat vs Full-Bus Interaction

Reuse existing Phase 7.1 conceptual policy behavior.

## Scenarios
- Per-seat + seats available:
  - `visible_and_bookable`.
- Per-seat + sold out/no seats:
  - `visible_and_sold_out`.
- Full-bus + virgin capacity/self-service allowed by policy:
  - `visible_and_bookable` (whole-bus mode CTA).
- Full-bus + partial holds/sales (no longer self-service):
  - `visible_assisted_only`.
- Published offer with no current executable tour binding:
  - `visible_view_only` + browse alternatives.

No Phase 7.1 policy redesign is introduced here.

---

## 8) Stable Public Entry Target

## Decision
Use stable Mini App route keyed by supplier offer identity.

Recommended shape:
- `/mini-app/supplier-offers/{supplier_offer_id}` (or equivalent stable slug mapping).

## Why
- Survives inventory and executable-link changes;
- keeps channel post persistent as discovery artifact;
- allows dynamic re-resolution of executable truth every time user opens.

## Behavior over time
- same link remains valid even when executable mapping changes;
- landing content remains anchored to showcase identity;
- CTA/action block reflects current policy state, not historical channel-time state.

---

## 9) Optional Layer A Tour Creation/Linking

## Recommendation
Do not require mandatory tour creation at publish time.

Allowed conversion patterns:
- link to existing Layer A tour;
- create Layer A tour later (explicit operational action);
- remain landing/view-only (no active executable binding).

## Default
`publish` guarantees visibility + landing availability contract, not guaranteed immediate bookability.

---

## 10) Customer Experience Expectations

## Case A: currently bookable
- user lands on supplier-offer landing;
- sees current executable availability;
- gets reserve/buy CTA.

## Case B: sold out
- user lands on same landing;
- sees sold-out state;
- gets browse alternatives CTA.

## Case C: full-bus not self-service now
- user lands on same landing;
- sees assisted-only explanation;
- gets alternatives CTA (assisted route hook can be added later).

No dead-end path in any case.

---

## 11) Publishing Order vs Conversion Readiness

## Accepted direction
Do not gate publication on booking readiness.

## Contract
- publication => channel discovery + stable Mini App landing;
- bookability evaluated dynamically on landing;
- landing valid before/during/after executable link availability windows.

---

## 12) Coupon/Promo Future Hook

Offer-specific coupons should attach to conversion/commercial layer, not raw channel text.

Recommended future hook:
- coupon metadata keyed to supplier-offer landing identity and/or active executable mapping policy;
- resolver decides applicability based on current actionability state.

Not implemented in this step.

---

## 13) Safest Implementation Sequence (Post-Design)

1. Add read-only Mini App supplier-offer landing endpoint/route keyed by stable supplier offer id.
2. Implement conversion-state resolver (`bookable/sold_out/assisted/view-only`) using existing policy truth and explicit mapping.
3. Update channel CTA generation to always target stable Mini App landing (both `Detalii` and `Rezervare` point to same landing contract).
4. Add UX states/CTAs in Mini App landing for all outcomes (never dead-end).
5. Add focused tests for dynamic state resolution and CTA behavior under mapping/policy changes.
6. Optional later: assisted flow hook, coupon hook, richer alternatives ranking.

---

## 14) Explicit Non-Goals / Postponed

- Supplier-offer auto retract/block cascade policy.
- Supplier status gating integration across supplier/offer bot surfaces.
- Broad RBAC/org redesign.
- Governance analytics/dashboard.
- Supplier-offer conversion bridge full implementation (this doc is design gate only).
- Layer A/RFQ/payment semantics redesign.
- Forced 1:1 `supplier_offer == tour` mapping.

---

## Design Summary

Use supplier offer as stable discovery identity and Mini App landing anchor; use Layer A + policy as dynamic actionability truth. Keep channel visibility durable, keep actionability dynamic, and preserve strict separation between publication object (`supplier_offer`) and execution object (`tour`).
