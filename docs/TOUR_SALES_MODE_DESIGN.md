# Tour Sales Mode Design

## Purpose
Define a design-first, tour-level sales-mode model for Tours_BOT before any schema, API, booking, Mini App, or bot implementation changes.

This track is intentionally separate from Phase 7 handoff/operator work. It introduces a new product/domain layer and must not be mixed into `group_followup_*` logic ad hoc.

## A. Problem Statement
- The current project already has seat-based reservation concepts such as `seats_total`, `seats_available`, and `seats_count`.
- That model is sufficient when the commercial action is "buy N seats".
- It is no longer sufficient once some carriers sell the entire bus as one commercial unit regardless of actual passenger count.
- If seat-based and whole-bus sales are mixed without an explicit tour mode, the product will confuse users:
  - a customer may see seat-style UI for a tour that is not sold seat-by-seat;
  - quantity-based pricing may imply that passenger count always defines price when it does not;
  - internal capacity data may be mistaken for the customer-facing pricing model.
- Some carriers think in terms of "sell this bus/run as a whole" rather than "sell seats one by one". The domain model needs to represent that directly.

## B. Proposed Core Concept
Introduce a tour-level source-of-truth field:

- `sales_mode`

Initial values:

- `per_seat`
- `full_bus`

`sales_mode` should be the tour-level source of truth that determines:

- how the tour is commercially sold;
- what Mini App read-side payloads should expose;
- what private bot wording and CTA shape should be used;
- which booking and pricing policies the backend/service layer applies.

This is a tour-level product/domain concept, not a UI-only flag and not a handoff-only concept.

## C. Domain Separation
The design should keep three concerns separate:

1. **Operational capacity / seat inventory**
   - how many passengers a bus can physically carry;
   - current free-vs-allocated seat inventory;
   - operational constraints for reservations, boarding, and fulfillment.

2. **Commercial pricing model**
   - how the carrier wants to charge;
   - per-passenger/seat pricing vs one fixed whole-bus price.

3. **Customer-facing booking mode**
   - what the user sees as the main purchase action;
   - whether the customer is selecting seats/quantity or requesting/buying the whole bus.

Key rules:

- Bus capacity is **not** the same thing as commercial sales mode.
- Passenger count does **not** always define price.
- `full_bus` must not pretend to be "many seats sold one by one".
- Existing seat inventory can remain operationally useful even when the commercial action is whole-bus purchase.

## D. Recommended Data Model Additions
Recommended minimal clean additions at the `tour` level:

- `sales_mode`
- `full_bus_price` (nullable; relevant when `sales_mode=full_bus`)
- `bus_capacity` (nullable/optional if the project needs an explicit operational capacity field beyond current seat inventory fields)

Relationship to existing seat-oriented fields:

- `seats_total`
  - remains an operational inventory/capacity-related field in the current model;
  - should not by itself define whether a tour is sold per seat or as a whole bus.
- `seats_available`
  - remains operational availability state;
  - should not be treated as the commercial source of truth for `full_bus`.
- `seats_count`
  - remains an order/waitlist/request quantity concept where relevant;
  - should not be assumed to be the pricing driver for every tour.

Recommended design stance:

- Keep the current seat-based model intact for operational accounting and current per-seat flows.
- Add `sales_mode` as the commercial source of truth rather than trying to overload `seats_*` semantics.
- Use `full_bus_price` for `full_bus` commercial configuration instead of deriving whole-bus pricing from seat math.
- Add `bus_capacity` only if the product needs a clearer operational field than existing `seats_total`; do not force a breaking replacement of current fields in the first rollout.

## E. Service-Layer Policy Implications
Business rules must remain backend-owned in the service layer. Mini App and private bot should reflect backend policy, not invent their own commercial logic.

### `per_seat`
- Seat/quantity selector is allowed.
- Price is per seat/passenger according to the existing seat-based model.
- Existing reservation and booking path remains the normal default.
- Current `seats_*` logic continues to matter directly for customer self-service.

### `full_bus`
- Self-service seat selector should be hidden or disabled as the main commercial action.
- The user is buying or requesting the whole bus, not incrementing seats as the core purchase model.
- Price is a fixed whole-bus price (`full_bus_price`), not `base_price * seats_count`.
- Passenger count may still exist for operational planning, but it does not define price.
- Initial rollout should likely be operator-assisted rather than instant fully self-service booking.
- Any future direct whole-bus booking flow should still be backend-governed by `sales_mode`, not by UI heuristics.

## F. Admin Implications
Admin/source-of-truth configuration should define:

- `sales_mode`
- pricing fields relevant to that mode
- capacity-related fields if needed operationally
- which tours are sold `per_seat` vs `full_bus`

Admin configuration must be the source of truth for client-facing behavior:

- Mini App should not guess sales mode from seat counts.
- Private bot should not infer whole-bus mode from a high capacity number.
- Backend policy should read admin-configured tour fields and expose the resulting behavior to clients.

## G. Mini App Implications
Mini App should render mode-aware read-side UX based on backend policy.

### `per_seat`
- Keep the normal seat-based purchase UI.
- Quantity selector remains valid.
- Pricing presentation remains seat/passenger-oriented.

### `full_bus`
- Present a whole-bus mode UI.
- Do not make seat-by-seat selection the primary commercial action.
- Show clear whole-bus wording, operational capacity, and fixed whole-bus price.
- CTA should be whole-bus request/booking oriented.
- If the first rollout is operator-assisted, the CTA should reflect that instead of pretending instant seat-style checkout exists.

## H. Private Bot Implications
### `per_seat`
- Current catalog/guided booking style remains valid.

### `full_bus`
- The bot must not pretend the customer is buying seats one by one.
- Copy and CTA should use whole-bus wording.
- First rollout should likely route into an operator-assisted path after catalog/detail discovery rather than force a fake seat-based self-service flow.

## I. Recommended Safe Rollout Path
Recommended order:

1. **Admin/source-of-truth fields**
   - define `sales_mode` and relevant pricing/configuration fields.
2. **Backend service-layer policy**
   - centralize rules for availability, pricing semantics, and allowed booking actions by mode.
3. **Read-side adaptation for Mini App and private bot**
   - expose mode-aware presentation and CTA behavior from backend-owned policy.
4. **Operator-assisted full-bus path**
   - support whole-bus demand without forcing an incomplete instant checkout.
5. **Only later, if needed, direct whole-bus booking flow**
   - add self-service only after the backend/domain model is stable.

Do **not** start with UI changes without backend policy and admin source of truth.

## J. Risks And Edge Cases
- Mixing capacity with pricing semantics.
- Pretending "N seats" always means "whole bus".
- Confusing customers with mixed seat/full-bus UX on the same type of screens.
- Adding Mini App logic ad hoc without admin-configured source of truth.
- Letting private bot and Mini App implement different commercial interpretations of the same tour.
- Trying to solve `full_bus` sales inside the existing Phase 7 handoff/operator flow instead of through a separate design and rollout sequence.
- Breaking current seat-based booking behavior by overloading existing `seats_*` fields instead of introducing an explicit `sales_mode`.

## Recommended Design Position
- Treat `sales_mode` as a first-class tour field.
- Preserve existing seat-based operational accounting.
- Add whole-bus commercial behavior through explicit backend policy, not UI guesswork.
- Roll out `full_bus` in an operator-assisted form first unless product explicitly approves full self-service.
