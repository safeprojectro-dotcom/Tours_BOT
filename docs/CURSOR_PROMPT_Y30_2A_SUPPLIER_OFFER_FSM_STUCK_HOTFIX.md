Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после current handoff/codebase.

Это узкий hotfix step.
Не переоткрывать архитектуру.
Не менять Layer A / RFQ / payment semantics.
Не менять supplier offer lifecycle semantics.
Не делать широкий refactor supplier onboarding/intake.
Исправить только подтверждённый FSM bug в supplier offer intake flow.

## Confirmed bug
In Telegram supplier offer intake flow, at the step:

`Trimite descriere scurtă rută/ofertă.`

the FSM gets stuck:
- user sends text messages
- bot gives no validation feedback
- bot does not transition to the next step
- bot appears to remain in the same state silently

This is a real FSM/runtime bug, not just user misunderstanding.

## Goal
Diagnose and fix the narrow supplier-offer intake FSM stuck behavior so that each input on this step results in exactly one of:
- successful save + transition to next step
- explicit validation error message + remain on current step

No silent no-op is allowed.

## Scope
Inspect and fix only the supplier offer intake FSM wiring around this step and adjacent transitions if needed.

## What to inspect
1. State definition for supplier-offer intake short-description step
2. Matching Telegram handler for that state
3. Router registration / handler ordering
4. Draft save/update path for that field
5. Transition to the next step after successful save
6. Explicit error handling for invalid input
7. Interaction with `Înapoi` / `Acasă`
8. Any broad text handlers that may swallow the message first
9. Any exception path that currently produces no user-visible reply

## Constraints
Do NOT:
- redesign the whole supplier offer intake flow
- redesign validation policy broadly
- redesign supplier moderation/publication
- touch Mini App conversion bridge work
- do unrelated cleanup

## Expected behavior after fix
For the short-description step:
- valid text -> saved -> next question shown
- invalid text -> explicit error shown
- no silent stuck state
- repeated random input must still produce visible response

## Likely files
Likely:
- supplier offer Telegram intake handler(s)
- bot FSM state definitions
- maybe messages text file
- focused tests only

## Before coding
Output briefly:
1. suspected root cause(s)
2. likely files to change
3. risks
4. why this is a narrow hotfix

## Required tests
Add/update focused tests for:
1. short-description valid text transitions to next step
2. invalid/edge input produces explicit feedback
3. no silent no-op on repeated messages
4. `Înapoi` and `Acasă` still behave correctly around this step

## After coding
Report exactly:
1. files changed
2. migrations none
3. tests run
4. results
5. root cause confirmed
6. what was fixed
7. compatibility notes