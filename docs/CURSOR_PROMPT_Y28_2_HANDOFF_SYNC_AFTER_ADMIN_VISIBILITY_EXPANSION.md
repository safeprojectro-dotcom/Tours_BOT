Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y28.2 Telegram admin approved/published visibility expansion implemented
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.

## Goal
Synchronize continuity docs after Y28.2 Telegram admin visibility expansion.

## What must be reflected

### 1. Telegram admin surfaces
Document that Telegram admin now has:
- `/admin_queue` for ready_for_moderation
- `/admin_approved` for approved/unpublished offers
- `/admin_published` for published offers

### 2. State-driven action separation
Document clearly:
- ready_for_moderation -> approve / reject
- approved/unpublished -> publish
- published -> retract

### 3. Boundaries preserved
Document clearly:
- approve != publish preserved
- no admin content editing
- no lifecycle redesign
- no scheduling
- no broader portal replacement

### 4. Next safe step
Set next safe step to:
- `Y29.2 — additive supplier profile status model`

### 5. Postponed items
Keep postponed:
- supplier profile moderation Telegram workspace
- supplier suspend/revoke implementation
- supplier status gating integration
- exclusion visibility policy
- scheduled publish
- mass moderation

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