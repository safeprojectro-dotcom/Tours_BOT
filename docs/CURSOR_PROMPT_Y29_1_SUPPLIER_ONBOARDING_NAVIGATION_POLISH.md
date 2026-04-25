Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- supplier Telegram onboarding already implemented
- supplier legal/compliance hardening already implemented
- `docs/SUPPLIER_ADMIN_MODERATION_AND_STATUS_POLICY_DESIGN.md` accepted
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не менять supplier profile lifecycle semantics.
Не делать broad redesign of onboarding.

## Goal
Implement narrow Telegram onboarding navigation polish for `/supplier`.

## Accepted design truth
Supplier onboarding should support safe navigation:
- `Înapoi` = previous step, preserving draft values in FSM
- `Acasă` = full cancel/reset, clearing onboarding FSM state/draft

This is UX/polish only.
No moderation, publication, or supplier-status redesign in this step.

## Exact scope

### 1. Add navigation controls
For the `/supplier` onboarding FSM, add:
- `Înapoi`
- `Acasă`

Keep them available consistently through the onboarding steps where text input / choice input is used.

### 2. Back behavior
`Înapoi` must:
- move the supplier one step back
- preserve already-entered onboarding data in FSM
- re-render the previous prompt cleanly
- avoid corrupting collected data

### 3. Home behavior
`Acasă` must:
- clear the onboarding FSM state
- clear the in-progress onboarding draft in FSM memory
- return the supplier to a safe neutral state with clear feedback

### 4. Keep current onboarding truth intact
Do NOT change:
- legal/compliance required fields
- onboarding submission semantics
- pending_review / approved / rejected semantics
- admin approve/reject behavior
- supplier offer flow
- publication flow

### 5. UX rules
- keep UX mobile-friendly
- avoid silent reset
- provide clear feedback on cancel/home
- keep wording aligned with existing supplier Telegram UX style

## What this step must NOT do
Do NOT:
- add supplier moderation in Telegram
- add suspend/revoke
- redesign onboarding fields
- redesign onboarding statuses
- add persistence changes
- add migrations
- touch offer moderation/publication semantics

## Likely files
Likely:
- `app/bot/handlers/supplier_onboarding.py`
- `app/bot/state.py`
- `app/bot/constants.py`
- `app/bot/messages.py`
- focused onboarding tests

Avoid unrelated files.

## Before coding
Output briefly:
1. current state
2. why Y29.1 is the next safe step
3. likely files to change
4. risks
5. what remains postponed

## Required tests
Add/update focused tests for:
1. back moves to previous onboarding step
2. back preserves draft FSM data
3. home clears FSM state
4. home returns safe feedback
5. existing onboarding submit path still works
6. no lifecycle semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier can now do
6. what remains postponed
7. compatibility notes

## Important note
This is a narrow onboarding navigation polish step only.
Do not silently expand into supplier moderation or supplier status policy implementation.