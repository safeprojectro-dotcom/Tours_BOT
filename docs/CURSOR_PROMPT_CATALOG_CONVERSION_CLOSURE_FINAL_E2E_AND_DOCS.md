# CURSOR_PROMPT_CATALOG_CONVERSION_CLOSURE_FINAL_E2E_AND_DOCS

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Это finalization step для блока:

SUPPLIER OFFER → CENTRAL MINI APP CATALOG CONVERSION CLOSURE

Не менять booking/payment/order/reservation.
Не менять Mini App UI.
Не менять Telegram showcase template.
Не менять media/photo pipeline.
Не добавлять auto-publish.
Не добавлять auto-activation.
Не добавлять hidden ORM triggers.
Не менять SupplierOffer lifecycle semantics без необходимости.

## Current implemented glue

Review package now includes `conversion_closure` with:

- has_tour_bridge
- has_catalog_visible_tour
- has_active_execution_link
- supplier_offer_landing_routes_to_tour
- bot_deeplink_routes_to_tour
- central_catalog_contains_tour
- next_missing_step

It is read-only and derives status from existing services.

## Goal

Prove the full explicit admin conversion chain with tests and docs.

The chain:

1. Supplier offer has required fields.
2. Packaging is approved_for_publish.
3. Admin creates/links Tour via existing bridge service/route.
4. Admin activates Tour for catalog via existing activation flow.
5. Supplier offer is published/eligible for execution link.
6. Admin creates active execution link or seeds it through existing service/repository.
7. Mini App central catalog contains linked Tour.
8. Supplier offer landing routes to linked Tour/actionability.
9. Bot `/start supoffer_<id>` routing resolves exact `/tours/{code}`.
10. Review package conversion_closure becomes complete / next_missing_step is null.
11. No booking/payment code changes.

## Required tests

Prefer a focused test file if appropriate:

tests/unit/test_supplier_offer_catalog_conversion_closure.py

or extend existing tests if project style strongly prefers it.

Add one E2E-style unit test that uses existing services/repositories as much as possible and proves:

- bridge creates or links a Tour from SupplierOffer
- activate-for-catalog makes Tour OPEN_FOR_SALE
- `/mini-app/catalog` service/read path includes Tour or MiniAppCatalogService returns it
- active execution link makes supplier offer landing actionable / routes to Tour
- B11 bot routing helper returns exact Tour Mini App URL
- review package `conversion_closure` has all booleans true and `next_missing_step is None`

Also add/confirm a negative test:

- approval alone does not create bridge/tour/catalog visibility/execution link
- review package shows the correct next_missing_step

Keep tests deterministic.

## Important safety assertions

Tests should make clear:

- central catalog visibility is Tour-driven and does not require execution link
- supplier offer landing / bot exact Tour routing requires active execution link
- full_bus does not become per-seat self-service if existing policy says assisted-only/view-only
- booking/payment services are not invoked or modified

## Required commands

Run:

python -m pytest tests/unit/test_supplier_offer_review_package.py -v
python -m pytest tests/unit/test_supplier_offer_tour_bridge_b10.py -v
python -m pytest tests/unit/test_supplier_offer_bot_start_routing_b11.py -v
python -m pytest tests/unit/test_private_entry_supoffer_start_hotfix.py -v
python -m pytest tests/unit/test_supplier_offer_track3_moderation.py -v
python -m pytest tests/unit/test_supplier_offer_showcase_ro.py -v

Also run any new/changed test file.

Then:

python -m compileall app alembic -q

## Docs update

Update briefly:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Document:

- Supplier Offer → Central Mini App Catalog Conversion Closure is now test-proven through explicit admin actions.
- Review package conversion_closure exposes the chain and next_missing_step.
- Approval alone still does not auto-create/link/activate/publish.
- Central catalog visibility is Tour-driven.
- Supplier offer landing / bot exact routing requires active execution link.
- Booking/payment remains Layer A and unchanged.

Do not rewrite docs.

## Final report

Report exactly:

1. Files changed
2. E2E-style test added/updated
3. What the E2E path proves
4. Negative test / approval-alone behavior
5. Mini App central catalog result
6. Supplier offer landing / bot deep-link result
7. full_bus/per_seat safety
8. Tests/checks run
9. Docs updated
10. Risks/follow-up