# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_MUTATION_BUTTONS_CONFIRMATION_DESIGN_DOCS

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only sync after C2B design.

Do not change app/.
Do not change tests/.
Do not change alembic/.
Do not change mini_app/.
Do not change runtime code.

## Context

C2B design decision:

Next safe mutating Telegram workflow slice should be packaging-only:

- add approve_packaging_for_publish from operator_workflow.actions
- only when action is enabled
- mandatory two-step confirmation
- re-read review-package before execution
- no duplicate approve_offer_moderation button because legacy Aprobă already exists
- do not add publish / activate catalog / execution link / create tour bridge
- do not add batch workflow button

Postponed:

- approve_offer_moderation workflow button until legacy Aprobă/Respinge consolidation
- create_tour_bridge until conversion-action slice
- activate_tour_for_catalog
- create_execution_link
- publish_showcase_channel

## Update only

- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

## Required notes

Add concise notes:

1. C2B design accepted.
2. Next implementation slice: C2B1 packaging approve only.
3. Telegram mutation policy:
   - every new mutating workflow button requires confirmation;
   - re-read review-package before execution;
   - execute only if action still enabled;
   - no hidden chained actions.
4. Existing Aprobă/Respinge remain legacy moderation buttons for now.
5. Do not duplicate approve_offer_moderation through operator_workflow until legacy consolidation.
6. Public/conversion actions postponed:
   - publish_showcase_channel
   - activate_tour_for_catalog
   - create_execution_link
   - create_tour_bridge for now.

Do not rewrite docs.

## Final report

Report:
1. Files changed
2. Policy notes added
3. Confirmation docs-only