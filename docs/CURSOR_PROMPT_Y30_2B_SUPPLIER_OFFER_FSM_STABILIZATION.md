Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current codebase and handoff.

Это узкий stabilization/hotfix step.
Не переоткрывать архитектуру.
Не менять supplier-offer lifecycle semantics.
Не менять moderation/publication semantics.
Не менять Mini App conversion bridge work.
Не менять Layer A / RFQ / payment semantics.

## Confirmed issue
After the previous hotfix for the description step, another real FSM silent-path bug is confirmed in the supplier offer intake flow:

At the step:
`Trimite titlul ofertei.`

the bot can still get stuck:
- user sends valid title text
- bot gives no visible response
- bot does not transition to the next step
- user sees silence

This confirms the problem is broader than a single description-step bug.

## Goal
Perform a narrow stabilization pass for supplier-offer intake FSM so that intake steps do not silently no-op.

For the inspected intake steps, every user input must result in exactly one of:
- successful save + transition + next prompt
- explicit validation feedback
- explicit processing-failed feedback

No silent return/no-op is allowed.

## Scope
Inspect and stabilize supplier-offer intake FSM handlers, especially:
- title step
- description step
- adjacent steps if they share the same failure pattern

Do not redesign the flow.
Do not broaden product scope.
Do not rewrite the whole intake architecture.

## What to inspect
1. Title-step handler
2. Description-step handler
3. Shared helper/update/save logic used by intake steps
4. Router/handler ordering
5. Any early returns with no visible feedback
6. Any exception paths swallowed silently
7. FSM transitions after successful save
8. Validation branches for empty/edge input
9. `Înapoi` / `Acasă` preservation across stabilized steps

## Expected behavior after fix
For stabilized steps:
- valid text -> saved -> next prompt shown
- invalid text -> explicit feedback
- internal processing issue -> explicit failure message
- repeated input -> always visible response, never silence

## Constraints
Do NOT:
- redesign intake fields
- redesign moderation/publication
- change DB schema
- touch Mini App conversion bridge
- do unrelated cleanup

## Likely files
Likely:
- `app/bot/handlers/supplier_offer_intake.py`
- `app/bot/messages.py`
- focused tests in `tests/unit/test_supplier_telegram_offer_intake_y22.py`

## Before coding
Output briefly:
1. suspected broader root cause
2. likely files to change
3. risks
4. why this is still a narrow stabilization step

## Required tests
Add/update focused tests for:
1. title valid text -> next step
2. title invalid/edge input -> explicit feedback
3. description valid text -> next step
4. description invalid/edge input -> explicit feedback
5. repeated invalid inputs on both steps -> never silent
6. `Înapoi` / `Acasă` remain correct around stabilized steps

## After coding
Report exactly:
1. files changed
2. migrations none
3. tests run
4. results
5. broader root cause confirmed
6. what was stabilized
7. compatibility notes