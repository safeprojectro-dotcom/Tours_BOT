Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y30.3 implemented
- supplier-offer landing now supports narrow execution activation into existing Layer A flow when safe authoritative linkage exists
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.

## Goal
Synchronize continuity docs after Y30.3 supplier-offer landing execution activation contract.

## What must be reflected

### 1. New execution activation capability
Document that published supplier-offer landing can now expose direct execution CTA only when:
- actionability_state is `bookable`
- authoritative linked executable target exists

Document that landing can now hand user into the existing Layer A flow through linked tour detail / current booking path.

### 2. Fail-safe preserved
Document clearly that no direct execution CTA is shown when:
- target is absent
- state is `sold_out`
- state is `assisted_only`
- state is `view_only`

### 3. Boundaries preserved
Document that Y30.3 still did NOT implement:
- auto-create Layer A tour
- auto-linking workflow
- coupon logic
- broad conversion activation workflow redesign
- publication pipeline redesign
- waitlist redesign
- Layer A / RFQ / payment semantics redesign

### 4. Compatibility
Document that:
- this is additive only
- landing payload gained optional execution activation fields
- existing clients can ignore them
- supplier_offer and tour remain separate entities
- activation uses only existing explicit linkage truth

### 5. Current operational limitation
Document clearly that without rows in `supplier_offer_execution_links`, the system correctly remains in safe fallback mode:
- landing works
- direct execution CTA is absent
- user can still browse catalog
This means scenario B/C is currently testable even when scenario A is not yet operationally available.

### 6. Next safe step
Set next safe step to:
- `Y30.4 — supplier-offer execution linkage workflow / linkage operations`

### 7. Postponed items
Keep postponed:
- auto-create tour
- auto-link workflow automation
- coupon logic
- broader conversion workflow redesign
- waitlist redesign
- publication redesign
- supplier status gating integration
- any Layer A / RFQ / payment redesign

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
Do not implement Y30.4 in this step.