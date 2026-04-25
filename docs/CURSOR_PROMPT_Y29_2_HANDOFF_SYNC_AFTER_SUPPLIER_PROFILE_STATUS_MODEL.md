Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y29.2 supplier profile status model implemented
- production migration `20260428_17` applied
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.

## Goal
Synchronize continuity docs after Y29.2 supplier profile status governance implementation.

## What must be reflected

### 1. Supplier profile governance truth
Document that supplier profile lifecycle now supports:
- pending_review
- approved
- rejected
- suspended
- revoked

Document that reactivation returns supplier profile back to approved.

### 2. Narrow admin governance surface now exists at backend truth level
Document that supplier profile governance now supports admin/service/API actions for:
- approve
- reject
- suspend
- reactivate
- revoke

Clarify that Telegram admin supplier workspace is not yet implemented in this step.

### 3. Scope boundaries preserved
Document clearly that Y29.2 did NOT implement:
- Telegram admin supplier moderation workspace
- supplier status gating integration across bot surfaces
- supplier offer auto retract/blocking cascade
- onboarding UX navigation polish here
- Layer A / RFQ / payment redesign

### 4. Existing compatibility
Document that:
- legacy approved suppliers remain compatible
- existing onboarding approve/reject path remains preserved
- supplier offer lifecycle semantics remain unchanged

### 5. Next safe step
Set next safe step to:
- `Y29.3 — Telegram admin supplier moderation workspace`

### 6. Postponed items
Keep postponed:
- Telegram supplier moderation workspace
- supplier status gating integration
- exclusion visibility policy / auto retract-block cascade
- broad RBAC/org redesign
- governance analytics/dashboard

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
Do not implement Y29.3 in this step.