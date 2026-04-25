Continue Tours_BOT strict continuation.

Task:
Implement the first safe runtime slice for operator/admin execution link workflow.

This step follows:
- Supplier conversion bridge gate (approved)
- Operator execution link workflow gate (approved)

==================================================
GOAL
==================================================

Allow operator/admin to:

1. Create execution link:
   supplier_offer -> tour

2. Replace execution link:
   - close previous link
   - activate new link

3. Close execution link:
   - no active link remains

==================================================
STRICT RULES
==================================================

Do NOT:
- auto-create tours
- modify tours structure
- change booking/payment logic (Layer A)
- change identity bridge
- change Mini App logic beyond already implemented resolver
- allow multiple active links per offer

Preserve:
- supplier_offer != tour
- visibility != bookability
- exactly ONE active link per supplier_offer
- Mini App uses link passively (read-side only)

==================================================
IMPLEMENTATION SCOPE
==================================================

Allowed:
- admin API endpoints (extend existing admin routes)
- service layer (supplier_offer_execution_link_service)
- repository logic if needed
- validation logic
- basic audit fields (timestamps/status)

==================================================
EXPECTED ENDPOINTS (if not already present)
==================================================

POST /admin/supplier-offers/{id}/link-tour
- create link

POST /admin/supplier-offers/{id}/replace-link
- replace active link

POST /admin/supplier-offers/{id}/close-link
- deactivate link

GET /admin/supplier-offers/{id}/links
- list history

==================================================
VALIDATION
==================================================

- supplier_offer must exist
- tour must exist
- only one active link allowed
- replacing must close previous link
- cannot create duplicate active link

==================================================
FAIL-SAFE
==================================================

If no active link:
Mini App must fallback to:
- view_only
- browse_catalog

==================================================
TESTS
==================================================

Add tests:
- create link
- replace link (old closed, new active)
- close link (no active remains)
- ensure only one active link exists

==================================================
AFTER CODING REPORT
==================================================

- files changed
- migrations (should be none unless absolutely needed)
- endpoints created
- tests executed
- confirmation that Mini App behavior unchanged