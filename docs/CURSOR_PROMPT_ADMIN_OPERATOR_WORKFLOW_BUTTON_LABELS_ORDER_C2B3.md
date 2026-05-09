# CURSOR_PROMPT_ADMIN_OPERATOR_WORKFLOW_BUTTON_LABELS_ORDER_C2B3

Ты продолжаешь проект Tours_BOT.

Cursor mode: Agent.

## Functional block

ADMIN OPERATOR WORKFLOW — C2B3

Rename/reorder current Telegram admin operator buttons according to accepted UX policy.

## Context

Accepted docs policy:

- Telegram admin card is not a developer console.
- Buttons should be 1–2 words, human-readable, sequential.
- No endpoint/action_code/enums in button labels.
- Preferred order:
  1. observe/read
  2. packaging
  3. legacy moderation
  4. Orders / Requests
  5. navigation
- Disabled workflow actions hidden.
- No new actions in this slice.

Currently implemented buttons include:

Read-only:
- review_package_refresh
- get_showcase_preview

Safe mutations:
- generate_packaging_draft
- approve_packaging_for_publish

Legacy moderation:
- Aprobă
- Respinge

Ops/nav:
- Orders
- Requests
- Previous / Next
- Back / Home

## Strict boundaries

Do not add new callbacks.
Do not add new actions.
Do not add publish button.
Do not add bridge button.
Do not add activate catalog button.
Do not add execution-link button.
Do not change callback prefixes.
Do not change action execution logic.
Do not change booking/payment/order/reservation.
Do not change Mini App UI.
Do not change Telegram showcase template.
Do not add migrations.
Do not call external AI.

This slice is label/order polish only.

## Goal

Update Telegram admin offer detail keyboard labels and order to be understandable for admins with mixed experience.

## Required label direction

Romanian labels:

- review_package_refresh -> `Actualizează`
- get_showcase_preview -> `Preview`
- generate_packaging_draft -> `Pregătește` or `Generează text`
- approve_packaging_for_publish -> `Aprobă text`
- legacy moderation approve -> `Aprobă oferta`
- legacy moderation reject -> `Respinge oferta`
- Orders -> keep if already short / localized, or `Comenzi`
- Requests -> keep if already short / localized, or `Cereri`
- Previous -> existing localized short label acceptable
- Next -> existing localized short label acceptable
- Back/Home -> existing localized short label acceptable

English fallback:

- Refresh
- Preview
- Prepare or Generate text
- Approve text
- Approve offer
- Reject offer
- Orders
- Requests

Pick the label that best fits existing i18n style.

## Required order

In the offer detail keyboard, preserve current behavior but order rows logically:

1. read-only workflow buttons:
   - Actualizează
   - Preview

2. packaging workflow buttons:
   - Pregătește / Generează text
   - Aprobă text

3. legacy moderation buttons:
   - Aprobă oferta
   - Respinge oferta

4. operational links:
   - Orders
   - Requests

5. navigation:
   - Previous / Next
   - Back / Home

Do not show empty rows.
Do not show disabled workflow actions.
Keep max 2 columns where existing layout supports it.

## Tests

Update tests to assert:

1. No raw technical labels in Telegram buttons:
   - no `review-package`
   - no `showcase`
   - no `packaging` if replaced by text/pachet copy
   - no snake_case action code
2. Read-only buttons appear before packaging buttons.
3. Packaging buttons appear before legacy moderation buttons.
4. Legacy `Aprobă` is disambiguated as `Aprobă oferta`.
5. Packaging approve is not bare `Aprobă`.
6. Existing callback prefixes and behavior remain unchanged.
7. Existing C2A/C2B1/C2B2 tests still pass.

Run:

python -m pytest tests/unit/test_operator_workflow_c2a_specs.py -v
python -m pytest tests/unit/test_operator_workflow_c2b1_specs.py -v
python -m pytest tests/unit/test_operator_workflow_c2b2_specs.py -v
python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -v
python -m pytest tests/unit/test_operator_workflow_telegram_format.py -v
python -m compileall app alembic -q

## Docs

Update briefly:

- docs/ADMIN_OPERATOR_WORKFLOW.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md

Mention:

- C2B3 implemented.
- Current Telegram buttons were renamed/reordered only.
- No new actions/callbacks were added.
- Labels now follow 1–2 word policy.
- Legacy moderation approve/reject are disambiguated.
- Public/conversion buttons remain postponed.

Do not rewrite docs.

## Final report

Report:
1. Files changed
2. Labels changed
3. Ordering changed
4. Confirmation no new actions/callbacks
5. Tests/checks run
6. Docs updated
7. Risks/follow-up