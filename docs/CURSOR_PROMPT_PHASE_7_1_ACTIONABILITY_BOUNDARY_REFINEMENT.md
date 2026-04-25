Context:
Phase 7.1 sales_mode (per_seat / full_bus) is partially implemented.
Core execution (Layer A), identity bridge, and user isolation are stabilized and accepted.

Strict constraints:
- DO NOT start supplier_offer → conversion bridge runtime implementation
- DO NOT modify booking/payment semantics
- DO NOT modify RFQ or supplier flows
- DO NOT touch identity bridge
- Keep fail-closed behavior

Objective:
Refine and formalize actionability boundaries for full_bus mode in Mini App and backend read-side.

Scope:
1. Define exact conditions when full_bus is:
   - bookable
   - assisted_only
   - view_only
   - blocked

2. Ensure consistency between:
   - Tour.sales_mode
   - seats_total / seats_available
   - existing reservations

3. Extend/readjust:
   - TourSalesModePolicyService (read-side only if possible)
   - Mini App actionability rendering (no UX redesign, only correctness)

4. Ensure:
   - No false-positive "bookable"
   - Fail-safe default → assisted_only or view_only

5. Add/extend unit tests for:
   - edge cases (partial seats, zero seats, full bus locked)
   - policy correctness

Out of scope:
- Supplier offers
- Execution linkage
- Admin workflows
- Incidents
- Coupons

Deliverables:
- minimal code changes (policy + read-side)
- tests
- small doc update if needed