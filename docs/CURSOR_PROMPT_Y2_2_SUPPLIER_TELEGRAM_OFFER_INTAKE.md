Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- UVXWA1 handoff sync
- Y2 Supplier Telegram Operating Model (design accepted)
- Y2.1 Supplier Telegram Identity Binding + Onboarding FSM + Admin Approve/Reject Gate (implemented and live-verified)
- current updated `docs/CHAT_HANDOFF.md`

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не делай broad redesign.

## Continuity base
Use as source of truth:
- current codebase
- `docs/CHAT_HANDOFF.md`
- `docs/SUPPLIER_TELEGRAM_OPERATING_MODEL_Y2.md`

Already accepted:
- supplier v1 = supplier entity + one primary Telegram-bound operator
- `/supplier` onboarding FSM exists
- onboarding states and admin approve/reject gate exist
- approved supplier is eligible for later supplier operating entry
- supplier offer intake must not bypass moderation/publication
- no direct creation of live Layer A tours from supplier bot intake
- no multi-operator org/RBAC in this step

## Exact next safe step

# Y2.2 — Supplier Telegram Offer Intake

### Goal
Allow an **approved supplier** to create and manage supplier offers through Telegram bot dialog/FSM in a narrow safe way.

This step should provide:
- explicit Telegram entry to supplier offer intake
- create draft supplier offer
- edit/restart draft safely
- explicit submit to moderation (`ready_for_moderation` or existing equivalent)
- safe bot feedback for draft/submitted states

This is supplier offer intake only.
Not publication.
Not supplier dashboard/stats.
Not RFQ supplier workspace redesign.
Not full supplier portal.

## What this block must implement

### 1. Supplier offer entry path in Telegram
Add a clear supplier bot entry for approved suppliers to start offer intake.

This may be through:
- command
- button/callback
- supplier menu path
- other narrow explicit entry

It must be:
- obvious
- gated to approved suppliers only

Pending/rejected/not-onboarded users must not enter approved offer flow.

### 2. Offer intake FSM
Implement a narrow Telegram FSM for supplier offer creation.

Use the already accepted supplier offer domain, not a parallel ad hoc structure.

Collect only the v1-safe offer fields needed for moderation-ready intake, for example:
- title / display title
- route / short description
- departure date/time
- basic commercial mode selection (where already supported by the supplier offer domain)
- pricing fields appropriate to the accepted supplier offer schema
- booking/payment mode fields already supported by the supplier offer domain
- optional conditions/restrictions
- optional media reference / photo handling only if the current architecture supports a safe narrow representation

Do not invent a huge media platform in this step.

### 3. Draft persistence
Supplier must be able to create a draft offer through Telegram and have it persisted in the existing supplier offer domain.

Important:
- this must reuse the existing supplier offer tables/services where possible
- do not create a second supplier-offer persistence model
- do not directly publish
- do not directly create live customer-facing tours in Layer A

### 4. Explicit submit to moderation
There must be an explicit final action that moves the draft into the existing moderation-ready state.

This should align with existing supplier offer lifecycle semantics:
- draft
- ready_for_moderation
- approved/rejected/published handled elsewhere

Do not bypass existing moderation/publication boundaries.

### 5. Supplier access gating
Only **approved suppliers** may proceed with offer intake.

Pending/rejected/not-onboarded users should get safe bot messages explaining they cannot use supplier operational offer entry yet.

### 6. Safe repeat behavior
Handle the narrow repeat cases safely:
- supplier starts a new offer while another draft is in progress
- supplier abandons flow and restarts
- supplier submits once and re-enters supplier offer flow
- do not create confusing duplicate half-drafts unless intentionally allowed by current domain rules

Choose the narrowest realistic safe behavior and document it in code/comments/tests.

### 7. Narrow Telegram feedback
Supplier should get clear bot feedback for:
- draft started
- field validation failures
- draft saved / submission accepted
- submitted for moderation
- gated because not approved

## What this block must NOT do

Do NOT:
- publish offers directly from Telegram
- bypass admin moderation
- create live Layer A tours directly from supplier bot input
- redesign supplier offer moderation/publication semantics
- implement supplier dashboard/stats
- implement supplier RFQ workspace redesign
- redesign supplier auth/platform
- add multi-operator org/RBAC
- redesign booking/payment/RFQ semantics

## Required architecture guardrails

### A. Reuse existing supplier offer domain
This step must plug into the already built supplier offer foundation and moderation lifecycle.
Do not fork it.

### B. Telegram is input surface only
Bot collects input and triggers service-layer actions.
Business rules stay in service layer.

### C. Preserve moderation boundary
Supplier Telegram intake ends at draft / ready_for_moderation.
Not at publish/live sale.

### D. Preserve Layer A boundary
No direct customer-live `Tour` creation in this step unless that already exists as the accepted supplier offer publication path and is only triggered by later admin-controlled publication.

### E. Preserve Mode separation
Do not mix supplier catalog offer intake with custom request / RFQ response logic.

## Files likely to change
Where appropriate:
- existing supplier offer services/schemas/repositories from Track 2/3 domain
- Telegram bot handlers/FSM/messages for supplier offer intake
- small admin/supplier read contracts only if strictly needed
- focused tests

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- custom request RFQ bridge execution services
- broad admin UI architecture
- broad Mini App booking/payment flows

## Before coding
Output briefly:
1. current project state
2. what Y2 and Y2.1 already decided
3. exact Y2.2 block goal
4. likely files to change
5. risks
6. what remains postponed

## Suggested implementation order
1. inspect existing supplier offer lifecycle/domain
2. define supplier-approved gate in Telegram entry
3. add narrow Telegram supplier offer FSM
4. persist draft through existing supplier offer services
5. add explicit submit-to-moderation action
6. add safe repeat/re-entry handling
7. add focused tests
8. keep docs updates minimal unless needed

## Tests required
Add focused tests only:
1. approved supplier can enter offer intake
2. pending/rejected supplier cannot enter approved offer flow
3. offer draft persists in existing supplier offer domain
4. submit moves offer to moderation-ready state
5. repeat/re-entry behavior is safe and deterministic
6. no booking/payment/RFQ semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier-facing behavior now works
6. moderation-boundary compatibility notes
7. postponed items

## Extra continuity note
This is Y2.2: supplier Telegram offer intake.
It is not permission to implement supplier publication bypass, supplier dashboard/stats, supplier RFQ workspace redesign, or broader auth/platform redesign in the same step.