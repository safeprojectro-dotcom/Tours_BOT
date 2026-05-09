# CURSOR_PROMPT_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a large functional block, but must be implemented safely.

Block name:

SUPPLIER OFFER → CENTRAL MINI APP CATALOG CONVERSION CLOSURE

---

## Business goal

Close the core BUSINESS-plan-v2 conversion process:

Supplier Offer
→ Admin review/approval
→ create/link Tour
→ activate Tour for central Mini App catalog
→ active execution link
→ supplier-offer landing and bot deep link route to exact Tour
→ Mini App central catalog shows Tour
→ booking/payment continues through existing Layer A

This is one of the most important business goals.

---

## Current checkpoint

Recently implemented:

GET /admin/supplier-offers/{offer_id}/review-package

It is read-only and aggregates:

- offer snapshot
- packaging axis
- moderation/showcase axis
- showcase preview
- bridge readiness
- active bridge / linked Tour
- catalog activation readiness
- execution-link readiness
- Mini App conversion preview
- warnings
- recommended_next_actions

Now we need to close the actual conversion chain after admin review.

---

## Critical architecture rules

Preserve strictly:

- Supplier Offer = raw/source facts.
- AI/deterministic packaging = draft only unless admin approved.
- Admin = final decision maker.
- Tour = customer-facing sellable catalog object.
- Mini App = execution truth.
- Layer A = booking/payment authority.
- Channel = marketing showcase.
- Bot = router/consultant.
- visibility != bookability.
- approved package != Telegram publish.
- Telegram published != Mini App catalog-visible.
- create/link Tour != open_for_sale.
- execution link != inventory/bookability by itself.
- No hidden ORM trigger from SupplierOffer to Tour.
- No AI-created Tour.
- No supplier bypass.
- No booking/payment/order changes.
- No automatic publish.
- No media pipeline.
- No sendPhoto/sendMediaGroup.
- No object storage.
- No Mini App UI redesign.

---

## Important product decision

Do not implement “approval automatically sends offer to catalog”.

Instead, preserve explicit admin gates:

1. Admin reviews package.
2. Admin approves packaging / moderation as needed.
3. Admin creates or links Tour.
4. Admin activates Tour for catalog.
5. Admin creates/ensures active execution link if needed.
6. Mini App catalog and supplier offer landing reflect execution truth.

It is acceptable to make these steps visible/testable and less fragile, but do not collapse them into an unsafe automatic trigger.

---

## Source files/docs to inspect first

Read/inspect:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/MINI_APP_UX.md
- docs/TESTING_STRATEGY.md

Code:

- app/api/routes/admin.py
- app/schemas/supplier_admin.py
- app/models/supplier.py
- app/models/tour.py
- app/models/enums.py
- app/services/supplier_offer_review_package_service.py
- app/services/supplier_offer_tour_bridge_service.py
- app/services/admin_tour_write.py
- app/services/supplier_offer_execution_link_service.py
- app/services/mini_app_supplier_offer_landing.py
- app/services/mini_app_catalog.py or equivalent catalog service
- app/services/mini_app_tour_detail.py
- app/bot/handlers/private_entry.py
- app/services/supplier_offer_bot_start_routing.py
- app/services/supplier_offer_deep_link.py
- app/repositories/supplier_offer_execution_link.py
- app/repositories/supplier_offer_tour_bridge.py if present

Tests:

- tests/unit/test_supplier_offer_review_package.py
- tests/unit/test_supplier_offer_tour_bridge_b10.py
- tests/unit/test_private_entry_supoffer_start_hotfix.py
- tests/unit/test_supplier_offer_bot_start_routing_b11.py
- tests/unit/test_bot_private_foundation.py
- tests/unit/test_supplier_offer_track3_moderation.py
- tests/unit/test_supplier_offer_showcase_ro.py
- any mini-app catalog/detail tests

Locate equivalent files if names differ.

---

## Step 1 — Audit current chain

Before changing code, audit current available endpoints/services and report internally in comments or final report:

1. How to create/link Tour from SupplierOffer today.
2. Preconditions:
   - packaging_status
   - lifecycle_status
   - missing fields
   - sales_mode
   - dates
   - price/currency
   - seats_total
3. How Tour is activated for Mini App central catalog.
4. What status makes Tour appear in `/mini-app/catalog`.
5. Whether active execution link is required for:
   - central catalog visibility
   - supplier offer landing
   - bot `/start supoffer_<id>`
6. How supplier-offer landing resolves actionability.
7. What is currently missing for end-to-end closure.

Do not duplicate existing behavior.

---

## Step 2 — Implement missing glue only

Implement only what is missing to make the chain testable and operable.

Possible acceptable changes:

### A. Readiness / status additions

If review-package lacks a clear enough central catalog closure status, extend it minimally with fields like:

```json
{
  "conversion_closure": {
    "has_tour_bridge": true,
    "has_catalog_visible_tour": true,
    "has_active_execution_link": true,
    "supplier_offer_landing_routes_to_tour": true,
    "bot_deeplink_routes_to_tour": true,
    "central_catalog_contains_tour": true,
    "next_missing_step": null
  }
}