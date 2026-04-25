Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y30.1 implemented
- stable Mini App landing for published supplier offers now exists
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.

## Goal
Synchronize continuity docs after Y30.1 stable Mini App supplier-offer landing implementation.

## What must be reflected

### 1. Stable Mini App supplier-offer landing now exists
Document that published supplier offers now have a stable Mini App entry route/landing.

Document that:
- users arriving from channel CTA no longer hit a dead end
- landing is read-only in this step
- landing is public only for published supplier offers
- unpublished offers return safe not-found behavior

### 2. Channel CTA behavior
Document that channel CTA now targets the stable supplier-offer Mini App landing rather than a fragile execution endpoint.

### 3. Scope boundaries preserved
Document clearly that Y30.1 did NOT implement:
- full actionability resolver
- direct booking/payment from supplier-offer landing
- auto-create/auto-link Layer A tour
- coupon logic
- broad publication redesign
- Layer A / RFQ / payment semantics redesign

### 4. Existing compatibility
Document that:
- Layer A booking/payment flows remain unchanged
- supplier_offer and tour remain separate entities
- existing catalog flow remains intact
- this step is additive read-side only

### 5. Next safe step
Set next safe step to:
- `Y30.2 — supplier-offer actionability resolver`

### 6. Postponed items
Keep postponed:
- sold_out / assisted_only / linked executable state resolver
- direct booking/payment activation from supplier-offer landing
- auto-link/create Layer A tour
- coupon logic
- supplier-offer conversion activation workflow
- broad publication redesign

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
Do not implement Y30.2 in this step.