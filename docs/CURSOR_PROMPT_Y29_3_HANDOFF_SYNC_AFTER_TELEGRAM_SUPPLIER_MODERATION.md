Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y29.3 Telegram admin supplier moderation workspace implemented
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.

## Goal
Synchronize continuity docs after Y29.3 Telegram admin supplier moderation workspace.

## What must be reflected

### 1. Telegram admin supplier workspace now exists
Document narrow Telegram admin supplier commands/surfaces:
- `/admin_supplier_queue`
- `/admin_suppliers`

### 2. Supplier admin actions
Document that Telegram admin can now perform supplier profile actions:
- approve
- reject with reason
- suspend with reason
- reactivate
- revoke with reason

### 3. Boundaries preserved
Document clearly:
- supplier profile moderation remains separate from supplier offer moderation
- no supplier-offer auto retract/blocking cascade yet
- no supplier status gating integration yet
- no Layer A / RFQ / payment redesign
- no broad RBAC/org redesign

### 4. Regression safety
Document that existing Telegram admin offer workspace remains unchanged and regression-tested.

### 5. Next safe step
Set next safe step to:
- `Y29.4 — supplier status gating integration`

### 6. Postponed items
Keep postponed:
- supplier exclusion visibility policy / auto retract-block cascade
- supplier status gating integration across supplier/offer surfaces
- broad RBAC/org redesign
- governance analytics/dashboard
- supplier-offer conversion bridge design/implementation

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
Do not implement Y29.4 in this step.