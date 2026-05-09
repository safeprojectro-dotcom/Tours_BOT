# CURSOR_PROMPT_ADMIN_REVIEW_PACKAGE_DOCS_SYNC

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only sync.

Не менять app/.
Не менять tests/.
Не менять alembic/.
Не менять mini_app/.
Не менять runtime code.

## Context

Implemented and verified:

GET /admin/supplier-offers/{offer_id}/review-package

It is part of:

ADMIN OFFER REVIEW & APPROVAL GATE — Slice 1

Tests passed:
- tests/unit/test_supplier_offer_review_package.py
- tests/unit/test_supplier_offer_tour_bridge_b10.py
- tests/unit/test_supplier_offer_track3_moderation.py
- tests/unit/test_supplier_offer_showcase_ro.py
Total: 53 passed
compileall app alembic: OK

Also fixed a missing import in app/api/routes/admin.py:
SupplierOfferSupplierNotificationService
This restores intended supplier notifications after moderation approve / publish / retract; no behavior change to review-package, bridges, catalog activation, or Mini App.

## Update briefly

Update only:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Add concise notes:

1. Admin Offer Review Package endpoint implemented:
   GET /admin/supplier-offers/{offer_id}/review-package

2. It is read-only and aggregates:
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

3. It does not:
   - publish
   - create/link Tour
   - activate catalog
   - create execution link
   - touch booking/payment

4. SupplierOfferSupplierNotificationService import fixed in admin routes, restoring intended notification calls after approve/publish/retract.

5. Next functional block:
   SUPPLIER OFFER → CENTRAL MINI APP CATALOG CONVERSION CLOSURE

Do not rewrite docs. Keep changes short.

## Final report

Report:
1. Files changed
2. Docs notes added
3. Confirmation docs-only