Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- narrow Mini App user-isolation hotfix implemented
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.

## Goal
Synchronize continuity docs after the Mini App user-isolation hotfix for `My bookings` / `My requests`.

## What must be reflected

### 1. Confirmed bug and fix
Document that a high-severity user isolation/privacy bug was confirmed in Mini App:
- different Telegram users could see the same data in `My bookings` / `My requests`

Document that the hotfix restored correct per-user isolation and removed/closed the unsafe shared path.

### 2. Scope boundaries preserved
Document clearly that this was a narrow identity/isolation hotfix only:
- no redesign of booking domain
- no redesign of requests domain
- no redesign of supplier conversion bridge
- no Layer A / RFQ / payment changes

### 3. Compatibility
Document that:
- valid user-facing Mini App flows continue to work
- data is now isolated per Telegram user
- unsafe fallback/shared identity behavior is no longer allowed in real runtime path

### 4. Next safe step
Document that after this hotfix the project returns to the current main roadmap/Design 1 track.
Reuse the already current next-step truth from handoff rather than inventing a different roadmap.

### 5. Postponed items
Keep broader roadmap/postponed items unchanged except for marking this bug closed.

## Files to update
Prefer only:
- `docs/CHAT_HANDOFF.md`
- optionally `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` if narrowly justified

## Before coding
Output briefly:
1. current continuity state
2. why sync is needed
3. files to update
4. scope boundaries

## After coding
Report exactly:
1. files changed
2. migrations none
3. tests not run (docs-only)
4. what was synchronized
5. current next safe step
6. compatibility notes

## Important note
This is docs sync only.
Do not reopen broader architecture in this step.