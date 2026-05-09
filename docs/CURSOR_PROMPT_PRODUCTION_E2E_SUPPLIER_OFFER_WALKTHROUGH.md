# CURSOR_PROMPT_PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH

Ты продолжаешь проект Tours_BOT.

## Cursor model / mode

Use the strongest available reasoning model.

Cursor mode: Agent.

This is a production/staging E2E smoke planning and verification block.

Do not implement new product features.
Do not change booking/payment/order/reservation logic.
Do not change Mini App UI.
Do not change Telegram showcase template.
Do not change media/photo pipeline.
Do not change SupplierOffer/Tour lifecycle semantics.
Do not add migrations.
Do not add AI wiring.

If you find a small obvious bug that blocks the smoke, do not silently fix it. Report it first unless it is clearly a one-line test/docs correction.

---

## Current milestone

BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION is closed.

Core conversion is test-proven:

Supplier Offer
→ Admin review/approval
→ create/link Tour
→ activate Tour for central Mini App catalog
→ active execution link
→ supplier-offer landing / bot deep link routes to exact Tour
→ Mini App central catalog shows Tour
→ booking/payment remains Layer A

Recent commits:
- 5d78dd2 — feat: close supplier offer catalog conversion chain
- 49496c8 — docs: audit business plan v2 after core conversion

---

## Goal

Create and execute, as far as possible from repo/API context, a production/staging E2E smoke checklist for a real or staging-like Supplier Offer.

The smoke must verify the operator path:

1. Supplier offer exists with required fields.
2. Admin review package is readable.
3. Packaging is approved_for_publish.
4. Moderation is approved.
5. Tour bridge creates/links Tour.
6. Tour is activated for Mini App catalog.
7. Showcase preview/publish path works if channel config is available.
8. Execution link is created.
9. Mini App catalog contains Tour.
10. Supplier offer landing resolves linked Tour.
11. Bot deep link supoffer_<id> routes to exact Tour.
12. Booking/payment path remains Layer A and is not altered by this smoke.

---

## Important

This step may be performed in one of two modes:

### Mode A — Dry-run / local API checklist

If production credentials/data cannot be safely used, create a precise operator checklist with commands and expected responses.

### Mode B — Real staging/prod smoke

If environment variables and safe test data are available, run actual API calls against production/staging and record results.

Do not invent results. If something cannot be executed, mark it as NOT RUN and explain what is needed.

---

## Source docs/code to inspect

Read:

- docs/BUSINESS_PLAN_V2_COMPLETION_AUDIT_AFTER_CORE_CONVERSION.md
- docs/HANDOFF_SUPPLIER_OFFER_TO_CENTRAL_CATALOG_CONVERSION_CLOSURE.md if present
- docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/TESTING_STRATEGY.md
- app/api/routes/admin.py
- app/schemas/supplier_admin.py
- app/services/supplier_offer_review_package_service.py
- app/services/supplier_offer_tour_bridge_service.py
- app/services/admin_tour_write.py
- app/services/mini_app_catalog.py
- app/services/mini_app_supplier_offer_landing.py
- app/services/supplier_offer_bot_start_routing.py
- tests/unit/test_supplier_offer_catalog_conversion_closure.py

---

## Required output document

Create:

```text
docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md