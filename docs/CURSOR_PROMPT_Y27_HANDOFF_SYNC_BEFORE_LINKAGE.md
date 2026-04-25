Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2.3 supplier moderation/publication workspace implemented
- Y2.1a supplier legal/compliance hardening implemented
- Y24 supplier basic operational visibility implemented
- Y25 supplier narrow operational alerts implemented
- Y27 authoritative offer→execution linkage design gate completed
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.
Не делать redesign.

## Goal
Synchronize continuity/handoff docs before Y27.1 implementation.

## What must be reflected

### 1. Current supplier subsystem scope
Document that supplier v1 now includes:
- onboarding
- legal/compliance hardening for pending supplier approval
- offer intake
- moderation/publication lifecycle
- retract path
- supplier workspace
- narrow operational visibility
- narrow operational alerts

### 2. Current read-side boundaries
Document clearly that supplier currently sees:
- own offers only
- statuses
- reject reason visibility
- publication/retraction visibility
- narrow operational visibility
- narrow alerts (`publication_retracted`, `offer_departing_soon`, `offer_departed`)

### 3. Current read-side limitations
Document clearly that supplier still does NOT get:
- customer PII
- customer list
- payment rows/provider details
- booking/payment controls
- finance dashboard
- booking-derived aggregate metrics unless authoritative linkage exists

### 4. Y27 design truth
Document that accepted design now says:
- authoritative execution truth = Layer A `Tour + Order`
- safe supplier booking-derived stats require explicit additive linkage
- recommended path = linkage table with one-active-link invariant
- legacy offers may remain unlinked
- richer booking-derived alerts remain postponed until linkage exists

### 5. Next safe step
Set next safe step to:
- `Y27.1 — supplier offer execution linkage persistence + admin link/unlink`

### 6. Boundaries still preserved
Reinforce:
- no Layer A booking/payment redesign
- no RFQ/bridge redesign
- no payment-entry/reconciliation redesign
- no customer PII exposure
- no supplier finance dashboard
- no broad portal/RBAC redesign

## Files to update
Prefer only:
- `docs/CHAT_HANDOFF.md`
- optionally `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` if narrowly justified

Do not mass-edit historical prompts.

## Before coding
Output briefly:
1. current continuity state
2. why sync is needed before Y27.1
3. files to update
4. what remains postponed

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
Do not implement Y27.1 in this step.