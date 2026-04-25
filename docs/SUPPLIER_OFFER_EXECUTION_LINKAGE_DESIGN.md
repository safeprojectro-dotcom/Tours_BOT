# Supplier Offer Execution Linkage Design (Y27)

## Status
- Design-only decision gate.
- No runtime implementation in this step.
- No migrations/tests/code changes in this step.

## Purpose
Define an explicit, authoritative linkage between published supplier offers and Layer A execution truth, so future supplier operational visibility can use real booking/order state without synthetic bot-layer math.

## Guardrails (preserved)
- No Layer A booking/payment redesign.
- No RFQ/bridge redesign.
- No payment-entry/reconciliation redesign.
- No Mode 2/Mode 3 merge.
- No customer PII exposure.
- No broad supplier portal/dashboard rewrite.

---

## 1) Source Of Execution Truth

### Decision
Supplier booking-derived operational visibility must rely on Layer A entities:
- `Tour` as execution capacity/source-of-availability anchor.
- `Order` rows for booking-state aggregates.

### Why
- `Tour.seats_total` / `Tour.seats_available` are already authoritative for capacity progress.
- `Order` already carries booking/payment/cancellation lifecycle needed for safe aggregate counters.
- This reuses existing core semantics instead of inventing a supplier-side shadow model.

---

## 2) Linkage Object

### Decision
Use a narrow additive linkage record, not implicit conventions:
- New linkage record concept: `supplier_offer_execution_links`.
- One supplier offer can have multiple historical link records over time.
- At most one active link per offer at a time.

### Recommended linkage shape (conceptual)
- `id`
- `supplier_offer_id` (FK -> `supplier_offers.id`)
- `tour_id` (FK -> `tours.id`)
- `link_status` (`active`, `replaced`, `retracted`, `invalidated`)
- `linked_at`, `unlinked_at`
- `link_note` (optional operator note)

### Why a linkage table (not just `supplier_offers.tour_id`)
- Handles replacement/republication history cleanly.
- Avoids losing prior mapping context when an offer is retracted/re-linked.
- Makes edge cases explicit (legacy unlinked, retracted but previously linked, link superseded).

### Mapping rules
- Link is explicit admin-controlled action.
- Link target must be exactly one `Tour` per active link.
- Concurrent many-to-many is disallowed in v1 linkage design.
- Historical one-to-many over time is allowed through closed/replaced link rows.

---

## 3) Signals Safely Derivable After Link Exists

For supplier-facing read-side only, no PII:

- `declared_capacity`: from `Tour.seats_total`
- `remaining_capacity`: from `Tour.seats_available`
- `occupied_capacity`: `seats_total - seats_available`
- `active_reserved_hold_seats`: sum `Order.seats_count` where:
  - `booking_status = reserved`
  - `payment_status = awaiting_payment`
  - `cancellation_status = active`
  - `reservation_expires_at > now`
- `confirmed_paid_seats`: sum `Order.seats_count` where:
  - `booking_status in (confirmed, ready_for_departure)`
  - `payment_status = paid`
  - `cancellation_status = active`
- `sold_out`: `remaining_capacity == 0`
- `first_confirmed_booking_signal`: derived from `confirmed_paid_seats > 0` (read marker);
  - push alert version requires separate dedupe/watermark policy in later step.
- `low_remaining_capacity_signal`: threshold-based marker (e.g. <= 10% or <= N seats), finalized in implementation step.

Notes:
- All signals are aggregate and tour-scoped through explicit active link.
- If no active link exists, supplier must see lifecycle-only + “execution stats unavailable”.

---

## 4) What Remains Unsafe Even With Linkage

Still out of scope for supplier surfaces:
- Customer identity (names, Telegram IDs, phone numbers).
- Order-level customer list views.
- Payment rows/provider payloads/transaction IDs.
- Admin-internal moderation notes beyond already allowed reject reason.
- RFQ-sensitive data outside already allowed supplier RFQ surfaces.
- Finance/accounting/reporting dashboards.
- Any mutation controls over bookings/payments.

---

## 5) Interaction With Current Lifecycle

### Approve vs publish
- `approved` remains moderation-only; does not imply execution link.
- Execution linkage is meaningful for operational visibility only when offer is `published` (or has historical link context for audit).

### Retract/unpublish
- On retract (`published -> approved`), active link should transition to non-active (`retracted`), but remain historically stored.
- Retracted offers should not emit live booking-derived operational alerts.

### Expired/departed offers
- Link may stay historically visible but marked inactive for forward operational alerts once tour departs/completes.

### Edited/republished offers
- Current supplier immutability for approved/published offers remains unchanged.
- If offer is republished and mapped to a different tour, prior link closes as `replaced`; new active link created.

### Legacy offers
- Existing offers start as unlinked by default.
- Backward-compatible behavior remains: lifecycle visibility works; booking-derived metrics stay unavailable until linked.

---

## 6) Migration vs No-Migration Recommendation

### Recommendation
Additive schema change is the cleanest safe path.

### Why not “no migration/read convention only”
- No authoritative field currently binds `supplier_offer` to `tour`.
- Heuristics (`title`, `supplier_reference`, dates, text matching) are unsafe and can misreport execution truth.
- Read-side convention without persisted link cannot support deterministic replacement/retract history.

### Narrow migration scope
- Add one linkage table (`supplier_offer_execution_links`) only.
- No changes to Layer A booking/payment tables/semantics.
- No changes to RFQ/bridge model.

---

## 7) Recommended Next Implementation Step (Narrow)

1. Add linkage persistence slice (migration + model + repository):
   - create linkage table with one-active-link invariant.
2. Add narrow admin-controlled link action(s):
   - set/replace active link for published supplier offer.
   - retract/close active link when publication is retracted.
3. Add supplier read-side aggregate visibility from active link only:
   - expose safe aggregate counters/markers listed above.
   - explicit fallback when no active link.
4. Keep booking-derived push alerts as a follow-up slice:
   - only after dedupe/watermark policy is defined.

This order preserves current behavior and introduces no hidden execution semantics.

---

## Explicitly Postponed
- Booking-derived notification engine redesign.
- Broad analytics/BI supplier dashboards.
- Supplier booking/payment controls.
- Any customer-level data exposure.
- Layer A semantic changes.
- RFQ/bridge semantic changes.
