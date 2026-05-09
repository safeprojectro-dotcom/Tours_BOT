# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_BUTTON_UX_POLICY_DOCS

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

Docs-only sync.

Do not change app/.
Do not change tests/.
Do not change alembic/.
Do not change mini_app/.
Do not change runtime code.

## Context

Telegram Admin Operator Workflow Button UX Policy was designed.

Key accepted decisions:

1. Telegram admin card is not a developer console.
2. Buttons must be short, human-readable, sequential, and safe for admins with mixed experience.
3. No snake_case action codes, endpoints, enums, HTTP methods in button labels.
4. Preferred order:
   - refresh
   - preview
   - generate packaging/text
   - approve packaging/text
   - legacy moderation approve/reject
   - Orders / Requests
   - navigation
5. Disabled workflow actions are hidden, not shown as disabled buttons.
6. Safe reads do not require confirmation.
7. Safe mutations require confirmation and re-read review-package before execution.
8. Conversion/public actions remain postponed:
   - create_tour_bridge
   - activate_tour_for_catalog
   - create_execution_link
   - publish_showcase_channel
9. Legacy Aprobă / Respinge remain for now, but must be disambiguated later from packaging approval:
   - legacy moderation approve should become Aprobă oferta
   - packaging approve should not be bare Aprobă
10. Next implementation slice should be rename/reorder only, no new actions.

## Update only

- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

## Required notes

Add concise notes:

- Telegram Button UX Policy accepted.
- Buttons should be 1–2 words, outcome/action oriented.
- No technical codes/endpoints/enums in labels.
- Current/future label direction:
  - review_package_refresh -> Actualizează / Refresh
  - get_showcase_preview -> Preview
  - generate_packaging_draft -> Generează text or Pregătește
  - approve_packaging_for_publish -> Aprobă text / Aprobă pachet
  - approve_offer_moderation legacy -> Aprobă oferta
  - reject -> Respinge oferta
- Preferred button order: observe/read → packaging → moderation → ops/navigation.
- Public/conversion buttons postponed.
- Next code slice: rename/reorder current Telegram buttons only; no new buttons/actions.

Do not rewrite docs.

## Final report

Report:
1. Files changed
2. Policy notes added
3. Confirmation docs-only