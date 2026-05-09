# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_C2B2_DOCS_SYNC

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only sync after C2B2 implementation.

Do not change app/.
Do not change tests/.
Do not change alembic/.
Do not change mini_app/.
Do not change runtime code.

## Context

ADMIN OPERATOR WORKFLOW — C2B2 implemented.

Telegram operator workflow now supports exactly one additional mutation action:

generate_packaging_draft

Behavior:
- button appears only when operator_workflow.actions has generate_packaging_draft enabled.
- first tap opens confirmation only.
- confirm re-reads review-package.
- confirm executes only if action is still enabled.
- uses SupplierOfferPackagingService.generate_and_persist.
- cancel does not mutate.
- refreshed offer card after success/failure handling.

Boundaries:
- no automatic packaging approval after generation.
- C2B1 approve_packaging_for_publish remains separate.
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
- C2B2 specs + C2B1 specs passed.
- Broader smoke to be run separately if needed.

## Update only

- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

## Required notes

Add concise notes:

1. C2B2 implemented.
2. Telegram workflow has generate_packaging_draft button with confirmation.
3. Confirm re-reads review-package and executes only if action is still enabled.
4. Only packaging draft generation is executed.
5. It does not approve packaging automatically.
6. No publish / bridge / catalog activation / execution-link buttons.
7. Legacy Aprobă / Respinge unchanged.
8. Next possible slice:
   - manual verification on a new real offer,
   - legacy moderation consolidation,
   - or create_tour_bridge later in conversion-action slice,
   - while conversion/public actions remain postponed.

Do not rewrite docs.

## Final report

Report:
1. Files changed
2. Notes added
3. Confirmation docs-only