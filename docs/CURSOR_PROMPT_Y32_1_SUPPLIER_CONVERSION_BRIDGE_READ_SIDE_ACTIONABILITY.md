Continue Tours_BOT strict continuation.

Task:
Implement the first safe runtime slice for Supplier Offer -> Conversion Bridge read-side actionability.

This is NOT auto-create-tour.
This is NOT booking/payment logic.
This is NOT supplier_offer == tour.

Read first:
- docs/CHAT_HANDOFF.md
- docs/SUPPLIER_CONVERSION_BRIDGE_IMPLEMENTATION_GATE.md
- docs/DESIGN_1_SUPPLIER_MARKETPLACE_ARCHITECTURE_CHECKPOINT.md
- docs/SUPPLIER_OFFER_EXECUTION_LINKAGE_DESIGN.md
- docs/SUPPLIER_OFFER_MINI_APP_CONVERSION_BRIDGE_DESIGN.md
- docs/PHASE_7_1_SALES_MODE_FULL_BUS_REVIEW_GATE.md

==================================================
GOAL
==================================================

Supplier offer Mini App landing / read-side resolver must correctly decide actionability:

1. If supplier_offer has active authoritative execution link to a tour:
   - resolve linked tour
   - use tour execution truth / sales_mode policy
   - show booking CTA only if linked tour is bookable

2. If supplier_offer has no active execution link:
   - do NOT show direct booking CTA
   - show assisted_only / view_only state

3. If link exists but linked tour is not bookable:
   - do NOT show direct booking CTA
   - show correct non-bookable state:
     - sold_out
     - assisted_only
     - view_only
     - disabled/unavailable if applicable

==================================================
STRICT RULES
==================================================

Do NOT:
- create tours automatically
- merge supplier_offer and tour
- change Layer A booking/payment
- change reservation/payment-entry semantics
- change identity bridge
- change RFQ semantics
- implement coupons
- implement incidents
- implement admin action workflows

Preserve:
- supplier_offer != tour
- visibility != bookability
- Mini App execution truth wins
- direct booking CTA only via active authoritative execution link
- fail-safe over false-positive bookability

==================================================
INVESTIGATE FIRST
==================================================

Before coding, report:
1. Which files/classes currently implement supplier offer landing.
2. Which model/repository/service handles supplier_offer_execution_links.
3. Whether active link lookup already exists.
4. Which actionability resolver currently exists.
5. How linked tour data is currently exposed to Mini App.
6. Exact minimal files to change.

==================================================
IMPLEMENTATION SCOPE
==================================================

Allowed changes:
- read-side service/resolver for supplier offer landing
- DTO/schema fields for actionability if already part of contract
- Mini App landing CTA rendering if it currently shows unsafe direct CTA
- focused unit tests

Expected output state for supplier offer landing:
- actionability_state
- has_execution_link
- linked_tour_id / linked_tour_code only if safe and already allowed
- execution_cta_enabled true only if linked tour is bookable
- fallback_cta when no safe execution

==================================================
EXPECTED STATES
==================================================

At minimum support:
- bookable
- assisted_only
- view_only
- sold_out
- unavailable
- disabled_by_incident only if already exists; otherwise leave postponed

Mapping:
- no active link -> assisted_only or view_only, depending existing policy
- active link + per_seat bookable -> bookable
- active link + per_seat sold out -> sold_out
- active link + full_bus bookable by Phase 7.1 policy -> bookable
- active link + full_bus partial -> assisted_only
- active link + full_bus sold out -> view_only/sold_out based existing policy
- invalid execution snapshot -> unavailable/blocked, no CTA

==================================================
TESTS
==================================================

Add or extend focused tests for:
1. supplier offer without link does not expose booking CTA
2. supplier offer with active link to bookable per_seat tour exposes booking CTA
3. supplier offer with active link to full_bus partial does not expose booking CTA
4. supplier offer with inactive/closed link does not expose booking CTA
5. supplier offer linked to sold out tour does not expose false booking CTA

Run:
- python -m compileall app mini_app
- focused relevant tests

==================================================
DOCS
==================================================

Update:
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if new non-blocking debt remains

Do not create broad new docs unless necessary.

==================================================
AFTER CODING REPORT
==================================================

Report:
- Current state before coding
- Files changed
- Migrations: none expected
- Tests run
- Exact actionability mapping implemented
- Compatibility notes
- What remains postponed