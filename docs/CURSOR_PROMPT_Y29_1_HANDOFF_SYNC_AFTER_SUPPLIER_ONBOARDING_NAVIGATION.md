Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y29.1 supplier onboarding navigation polish implemented
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.

## Goal
Synchronize continuity docs after Y29.1 supplier onboarding navigation polish.

## What must be reflected

### 1. Supplier onboarding UX
Document that `/supplier` onboarding now supports:
- `Înapoi`
- `Acasă`

### 2. Back/Home semantics
Document clearly:
- back = previous step with in-memory FSM draft preserved
- home = full onboarding FSM reset/cancel

### 3. Boundaries preserved
Document clearly that this step did NOT change:
- onboarding required fields
- onboarding approval lifecycle
- supplier status model
- supplier offer lifecycle
- publication flow
- Layer A / RFQ / payment semantics

### 4. Next safe step
Set next safe step to:
- `Y28.2 — Telegram admin approved/published visibility expansion`

### 5. Postponed items
Keep postponed:
- supplier Telegram moderation workspace
- supplier suspend/revoke implementation
- supplier status gating integration
- exclusion visibility policy

## Files to update
Prefer only:
- `docs/CHAT_HANDOFF.md`
- optionally `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` if narrowly justified

## Before coding
Output briefly:
1. current continuity state
2. why sync is needed
3. files to update
4. postponed items

## After coding
Report exactly:
1. files changed
2. migrations none
3. tests not run (docs-only)
4. what was synchronized
5. next safe step
6. postponed items

## Important note
This is docs sync only.
Do not implement the next feature in this step.