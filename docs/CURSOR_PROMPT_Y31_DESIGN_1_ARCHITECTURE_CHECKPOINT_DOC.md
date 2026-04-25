Continue Tours_BOT strict continuation.

Task:
Create an intermediate architecture checkpoint document for Design 1 before moving to the next tracks.

Create:

docs/DESIGN_1_SUPPLIER_MARKETPLACE_ARCHITECTURE_CHECKPOINT.md

This is documentation-only.
Do not change runtime code.

Document must formalize:

1. Current accepted state after Mini App identity stabilization
- Mini App identity bridge works
- user-scoped flows work:
  - My bookings
  - My requests
  - Settings
  - custom request creation
  - reservation/payment flow
- fail-closed privacy model is preserved

2. Design 1 principles
- Supplier Offer
- Public Showcase
- Conversion Bridge
- Execution Truth
- visibility != bookability
- channel showcase softer
- Mini App execution truth strict and current
- supplier_offer != tour
- explicit authoritative linkage only

3. Entity separation
- supplier_offers
- tours
- supplier_offer_execution_links
- custom_marketplace_requests
- orders/bookings

4. Admin/ops principle
- user self-service view != admin operational view
- My bookings / My requests remain user-scoped
- admin must get separate operational surfaces for all bookings and all requests

5. Safe implementation order from here
A. Phase 7.1 continuation:
   - sales_mode / full_bus logic
B. Supplier → Conversion Bridge:
   - execution linkage
   - actionability states
   - safe Mini App landing
C. Operator workflows:
   - process requests
   - close/resolve/reassign
   - admin operational visibility/actions

6. Explicit non-goals
- no broad refactor
- no Layer A rewrite
- no unsafe identity fallback
- no merging supplier_offer and tour
- no admin access through user-scoped screens
- no coupon/incident automation before design gate

7. Recommended next tracks
- ADMIN_OPERATIONAL_VISIBILITY_FOR_BOOKINGS_AND_REQUESTS
- PHASE_7_1_SALES_MODE_FULL_BUS_CONTINUATION
- SUPPLIER_CONVERSION_BRIDGE_EXECUTION_LINKAGE
- OPERATOR_REQUEST_WORKFLOW

Also update:
- docs/CHAT_HANDOFF.md with a short reference to this checkpoint.

Do not update runtime code.
Do not add migrations.