# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_SLICE_B_CORRECTION

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

This is a correction/finalization for ADMIN OPERATOR WORKFLOW Slice B.

Do not touch unrelated HANDOFF_* files.
Do not touch old CURSOR_PROMPT_* files.
Do not change booking/payment/order/reservation.
Do not change Mini App UI.
Do not change publish behavior.
Do not change Tour bridge/catalog activation behavior.
Do not add migrations.
Do not add Telegram buttons.
Do not add web UI.
Do not add batch endpoints.

## Current implemented state

Slice B implementation exists:

- app/schemas/supplier_admin.py
- app/services/supplier_offer_operator_workflow.py
- app/services/supplier_offer_review_package_service.py
- tests/unit/test_supplier_offer_review_package.py

review-package now includes read-only operator_workflow.

## Required correction

### 1. Normalize danger_level enum/string values

Use these exact values:

- safe_read
- safe_mutation
- conversion_enabling
- public_dangerous

Update code/tests/docs if needed.

Mapping:

- review_package, showcase_preview, verify_mini_app_catalog, verify_supplier_offer_landing, verify_bot_deep_link → safe_read
- generate_packaging, approve_packaging, approve_moderation, create_tour_bridge → safe_mutation
- activate_tour_for_catalog, create_execution_link → conversion_enabling
- publish_showcase → public_dangerous

publish_showcase must also have:

- requires_confirmation = true
- enabled only when showcase_preview.can_publish_now is true
- public_dangerous even if currently disabled

### 2. Make sure read-only boundary is preserved

GET review-package must not execute any action.

No POSTs from operator_workflow builder.

### 3. Docs sync

Update briefly only:

- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Mention Slice B implemented:

- review-package includes read-only operator_workflow
- state / primary_next_action / actions / danger_level / confirmation / endpoint hints
- no action execution
- no Telegram buttons / web UI / batch actions

Do not rewrite docs.

### 4. Tests

Run:

python -m pytest tests/unit/test_supplier_offer_review_package.py -v
python -m pytest tests/unit/test_supplier_offer_content_quality_review.py -v
python -m pytest tests/unit/test_supplier_offer_ai_public_copy_fact_lock.py -v
python -m pytest tests/unit/test_supplier_offer_catalog_conversion_closure.py -v
python -m pytest tests/unit/test_supplier_offer_showcase_ro.py -v
python -m compileall app alembic -q

If there is a dedicated operator workflow test file, run it too.

## Final report

Report:

1. Files changed
2. danger_level values fixed
3. operator_workflow remains read-only
4. Docs updated
5. Tests/checks run
6. Any unrelated HANDOFF/CURSOR files touched? yes/no