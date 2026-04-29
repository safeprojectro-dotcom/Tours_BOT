# HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE

Project: Tours_BOT

## Functional block

SUPPLIER OFFER → CENTRAL MINI APP CATALOG CONVERSION CLOSURE

## Goal

Close the core BUSINESS-plan-v2 process:

Supplier Offer
→ Admin review/approval
→ create/link Tour
→ activate Tour for central Mini App catalog
→ active execution link
→ supplier-offer landing / bot deep link routes to exact Tour
→ Mini App central catalog shows Tour
→ booking/payment through existing Layer A

## Critical principles

- Supplier Offer approval alone does not auto-create bookable customer product.
- Packaging approval, moderation approval, channel publish, Tour bridge, catalog activation, execution link are separate gates.
- Channel showcase is marketing.
- Mini App catalog is execution truth.
- Layer A remains booking/payment authority.
- No hidden ORM triggers.
- No automatic publish.
- No automatic activation.
- Admin actions remain explicit.

## Implementation status (read-only observability)

- **`GET /admin/supplier-offers/{offer_id}/review-package`** aggregates bridge readiness, linked tour catalog activation preview, execution links, Mini App conversion preview, warnings, and **`recommended_next_actions`** (no mutations).
- **`conversion_closure`** (same response) summarizes explicit gates: tour bridge present, linked tour **`open_for_sale`**, active execution link, landing exposes linked tour, B11 bot deep-link routes to **`/tours/{code}`**, central catalog inclusion (**`OPEN_FOR_SALE`** + customer visibility window), plus **`next_missing_step`** when any gate is still open. **`next_missing_step`** is **`null`** only when all those flags are true — it does **not** replace admin actions; it makes the chain testable and inspectable.
- Gates remain **separate**; nothing here auto-publishes, auto-activates, or auto-links.

## Expected outcome after implementation

A tested explicit admin path exists:

1. Review supplier offer.
2. Approve packaging/moderation as needed.
3. Create/link Tour.
4. Activate Tour for catalog.
5. Ensure active execution link.
6. Verify Tour appears in Mini App catalog.
7. Verify supplier offer landing and bot deep link route to exact Tour.
8. Verify booking/payment path remains existing Layer A.

## Next after this block

After closure, move to either:

- Production E2E smoke checklist for real supplier offer, or
- Admin workflow consolidation/UI, or
- AI-approved public copy wiring.

Do not start next block automatically.