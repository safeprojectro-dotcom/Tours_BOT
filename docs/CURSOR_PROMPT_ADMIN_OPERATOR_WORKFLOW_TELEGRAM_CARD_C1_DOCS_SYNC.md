# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_TELEGRAM_CARD_C1_DOCS_SYNC

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only sync after Slice C1 implementation.

Do not change app/.
Do not change tests/.
Do not change alembic/.
Do not change mini_app/.
Do not change runtime code.

## Context

ADMIN OPERATOR WORKFLOW — Slice C1 implemented.

Telegram admin offer card now displays read-only operator_workflow guidance from SupplierOfferReviewPackageService.review_package():

- state
- primary_next_action
- danger/confirmation/endpoint hint
- blocking reasons
- workflow warnings
- footer saying guidance is read-only

No POST actions are executed by the formatter.
No Telegram mutation buttons were added.
No publish/bridge/activate/link action buttons were added.
No booking/payment/Mini App/showcase behavior changed.

Files implemented earlier:
- app/bot/supplier_offer_operator_workflow_telegram.py
- app/bot/handlers/admin_moderation.py
- app/bot/messages.py
- tests/unit/test_operator_workflow_telegram_format.py

Tests passed:
- tests/unit/test_operator_workflow_telegram_format.py
- tests/unit/test_supplier_offer_review_package.py
- tests/unit/test_telegram_admin_moderation_y281.py
Total 57 passed
compileall app alembic OK

## Update only

- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

## Required notes

Add concise notes:

1. Slice C1 implemented.
2. Telegram admin offer card displays operator_workflow from review-package.
3. Display-only: no actions executed from Telegram card.
4. No publish/bridge/activate/execution-link buttons added yet.
5. Next possible slice: Telegram action buttons consuming operator_workflow.actions, starting with safe/low-risk actions and explicit confirmation.

Do not rewrite docs.

## Final report

Report:
1. Files changed
2. Docs notes added
3. Confirmation docs-only