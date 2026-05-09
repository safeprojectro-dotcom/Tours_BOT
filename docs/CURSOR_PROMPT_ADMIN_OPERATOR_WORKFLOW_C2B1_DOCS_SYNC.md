# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_C2B1_DOCS_SYNC

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only sync after C2B1 implementation.

Do not change app/.
Do not change tests/.
Do not change alembic/.
Do not change mini_app/.
Do not change runtime code.

## Context

ADMIN OPERATOR WORKFLOW — C2B1 implemented.

Telegram operator workflow now supports exactly one mutation action:

approve_packaging_for_publish

Behavior:
- button appears only when operator_workflow.actions has approve_packaging_for_publish enabled.
- first tap opens confirmation only.
- confirm re-reads review-package.
- confirm executes only if action is still enabled.
- uses SupplierOfferPackagingReviewService.approve.
- passes accept_warnings for needs_admin_review.
- reviewed_by = telegram:{admin_id}.
- cancel does not mutate.
- refreshed offer card after success.

Boundaries:
- no approve_offer_moderation workflow button.
- legacy Aprobă / Respinge unchanged.
- no publish button.
- no create_tour_bridge button.
- no activate catalog button.
- no execution link button.
- no batch workflow.
- no booking/payment/Mini App changes.
- no migrations.

Tests:
- C2B1 specs + C2A specs + Telegram admin moderation passed.
- Broader smoke to be run separately if needed.

## Update only

- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

## Required notes

Add concise notes:

1. C2B1 implemented.
2. Telegram workflow has approve_packaging_for_publish button with confirmation.
3. Confirm re-reads review-package and executes only if action is still enabled.
4. Only packaging approval is executed.
5. No publish / bridge / catalog activation / execution link buttons.
6. Legacy Aprobă / Respinge unchanged.
7. Next possible slice:
   - generate_packaging_draft with confirmation, or
   - legacy moderation consolidation,
   - while conversion/public actions remain postponed.

Do not rewrite docs.

## Final report

Report:
1. Files changed
2. Notes added
3. Confirmation docs-only