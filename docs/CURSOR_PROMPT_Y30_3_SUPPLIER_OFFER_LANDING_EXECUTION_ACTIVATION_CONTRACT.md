Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y30 design accepted
- Y30.1 stable Mini App published supplier-offer landing implemented
- Y30.2 supplier-offer actionability resolver implemented
- recent supplier-offer intake FSM hotfixes/stabilization are closed
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не сливать `supplier_offers` и `tours`.
Не делать broad publication redesign.

## Goal
Implement the next narrow bridge step:

**direct execution activation contract from supplier-offer landing**

This step should define and implement the minimal safe path by which a supplier-offer landing can move the user toward existing booking/payment execution truth when — and only when — such execution truth is safely available.

## Accepted design truth
- Published supplier offers remain visible in Telegram channel as showcase content.
- Mini App landing already exists and shows actionability.
- Visibility != bookability.
- `supplier_offer` remains separate from Layer A `tour`.
- Direct execution from landing must only be allowed when safe executable truth already exists.
- No unsupported booking math may be invented.

## Exact scope

### 1. Narrow execution activation contract
Implement the narrowest safe contract for what happens when supplier-offer landing is currently `bookable`.

The contract must answer:
- what object does landing point to for execution?
- under what condition is execution allowed?
- how does landing route user into existing Layer A booking/payment flow?

### 2. Existing truth only
Execution activation must only use already existing authoritative truth, for example:
- linked executable Layer A tour if already present
- existing booking/payment entry mechanisms already in system

Do NOT create new booking/payment semantics.

### 3. Safe gating
If landing cannot safely resolve to existing executable truth, it must not offer direct execution.
Fail-safe remains:
- `view_only`
- `assisted_only`
- `sold_out`

### 4. Landing CTA behavior
For `bookable` state, replace placeholder catalog-only CTA with a safe path into the existing booking flow, but only when authoritative execution target is available.

For other states:
- preserve non-booking behavior
- preserve catalog fallback

### 5. Minimal linkage usage
Reuse existing explicit linkage truth if already present in the project.
Do not invent uncontrolled automatic mapping.
Do not force auto-create tour in this step.

### 6. API / UI shape
Expose the narrowest additional landing payload/UI behavior needed for:
- execution target available
- execution target absent

### 7. No broad rollout
Do NOT implement:
- auto-create Layer A tour
- auto-linking workflow
- coupon logic
- broad conversion workflow redesign
- waitlist redesign
- publication pipeline redesign

## Expected behavior
### Case A: published supplier offer + safe executable target exists
User opens landing and can continue into existing booking/payment flow through an explicit CTA.

### Case B: published supplier offer but no executable target
Landing remains informational/actionable only according to prior states, with catalog/help fallback.

### Case C: sold out / assisted only / view only
No direct execution CTA appears.

## Likely files
Likely:
- `app/services/mini_app_supplier_offer_landing.py`
- maybe linkage/execution helper reuse
- `app/schemas/mini_app.py`
- `app/api/routes/mini_app.py`
- `mini_app/api_client.py`
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- focused tests

Avoid unrelated subsystems.

## Before coding
Output briefly:
1. current state
2. why Y30.3 is the next safe step
3. likely files to change
4. risks
5. what remains postponed

## Required tests
Add/update focused tests for:
1. bookable landing with authoritative execution target exposes execution CTA
2. bookable landing without execution target fails safe and does not expose false execution
3. sold_out / assisted_only / view_only still avoid execution CTA
4. existing booking/payment semantics remain unchanged
5. existing landing behavior remains intact when execution is absent

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what user can now do from supplier-offer landing
6. what remains postponed
7. compatibility notes

## Important note
This step is about safe activation into existing execution truth only.
Do not silently implement auto-create tour, auto-linking workflow, or coupon logic.