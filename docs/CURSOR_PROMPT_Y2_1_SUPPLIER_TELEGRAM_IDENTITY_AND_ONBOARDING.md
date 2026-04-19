Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- handoff/docs sync checkpoint
- U1–U3
- V1–V4
- W1–W3
- X1–X2
- A1
- A2
- A3
- Y2 supplier Telegram operating model design gate
- key hotfixes and production fixes

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не делай broad redesign.

## Continuity base
Считать источниками истины:
- current codebase
- updated `docs/CHAT_HANDOFF.md`
- `docs/CHECKPOINT_UVXWA1_SUMMARY.md`
- `docs/SUPPLIER_TELEGRAM_OPERATING_MODEL_Y2.md`

Уже принято по Y2:
- v1 supplier model = supplier entity + one primary Telegram-bound operator
- Telegram user binding is the practical operating entry anchor
- onboarding goes through Telegram FSM
- supplier operational access only after explicit admin approve
- supplier offer intake must not bypass moderation
- no direct creation of live Layer A tours from supplier bot intake
- no multi-operator org/RBAC in this step

## Exact next safe step

Implement a medium-sized coherent block:

# Y2.1 — Supplier Telegram Identity Binding + Onboarding FSM + Admin Approve/Reject Gate

### Goal
Create the first real supplier-through-bot operating entry:
- supplier starts in Telegram
- completes a narrow onboarding FSM
- supplier profile/submission is persisted
- admin can approve or reject the onboarding
- only approved supplier can proceed to later supplier functions

This is the first supplier-entry implementation step.
Not supplier offer intake yet.
Not full supplier portal.
Not a broad auth redesign.

## Block scope

### 1. Telegram supplier entry in bot
Add a clear supplier entry path in the bot, so a Telegram user can start supplier onboarding intentionally.

This may be through:
- command
- callback/button
- narrow entry screen/menu
- or another minimal explicit Telegram entry path

Keep it narrow and obvious.

### 2. Supplier onboarding FSM
Implement a minimal Telegram onboarding flow collecting only the v1-safe fields decided in Y2, such as:
- company/display name
- contact info
- region
- basic capability declaration
- optional fleet summary

Do not overcollect.
Do not build a KYC platform in this step.

### 3. Persist supplier onboarding submission
On successful onboarding submission:
- persist supplier/onboarding data in the appropriate supplier domain
- bind the primary Telegram user id as the supplier operator/access anchor
- mark submission as pending admin review / equivalent safe state

Do not grant supplier operational publishing powers yet.

### 4. Admin approve/reject gate
Implement the narrow admin action needed so onboarding can move from pending to approved/rejected.

Use the existing admin architecture style.
Keep it narrow and explicit.

This can be:
- admin API route(s)
- minimal admin read visibility if needed
- minimal status change only

Do not redesign admin panel.

### 5. Access gate behavior
Approved supplier:
- becomes eligible for future supplier operating entry points

Pending/rejected supplier:
- cannot proceed as approved supplier
- should receive safe, human-readable bot messaging

### 6. Narrow Telegram feedback
Supplier should get safe Telegram feedback for:
- onboarding submitted
- already pending
- approved
- rejected (at least safe status messaging, even if full notification handling is postponed)

This can be minimal in this step.

## What this block must NOT do

Do NOT:
- implement supplier offer submission yet
- implement supplier dashboard/stats yet
- implement supplier RFQ workspace yet
- redesign supplier auth broadly
- add multi-operator organization model
- bypass admin moderation
- create live Layer A tours
- change booking/payment/RFQ semantics
- build a broad document/KYC workflow

## Likely files/modules to touch

Where appropriate:
- supplier models/schemas/services already existing in Track 2 domain
- Telegram bot handlers/FSM/messages for supplier onboarding
- narrow admin API/read path for approve/reject
- focused tests

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services
- Mini App booking/payment code
- broad admin portal architecture
- supplier offer publication logic beyond access gating

## Required design guardrails

### A. Telegram is entry anchor, not business-logic owner
Bot collects input and routes actions.
Backend/service layer remains the source of truth.

### B. Approval gate is mandatory
Supplier onboarding submission must not auto-approve into operational publish rights.

### C. Keep supplier v1 simple
One supplier entity + one primary Telegram-bound operator.
No roles matrix in this step.

### D. No moderation bypass
This step is about identity/onboarding, not about skipping offer moderation/publication.

### E. Preserve privacy and safe access
Do not expose admin-only or customer-sensitive information in supplier onboarding flow.

## Before coding
Output briefly:
1. current project state
2. what Y2 already decided
3. exact Y2.1 block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. inspect existing supplier domain objects from Track 2
2. decide the narrowest safe way to represent onboarding/pending/approved/rejected
3. add Telegram supplier entry point
4. add onboarding FSM
5. persist submission + Telegram binding
6. add narrow admin approve/reject action
7. add safe bot feedback states
8. add focused tests
9. keep docs updates minimal unless needed

## Tests required

Add focused tests only:
1. supplier can start onboarding through Telegram entry path
2. onboarding submission persists expected v1 fields
3. Telegram user id binding is stored correctly
4. pending supplier cannot be treated as approved
5. admin approve/reject path works as intended
6. approved supplier state is distinguishable from pending/rejected
7. no booking/payment/RFQ semantics are affected

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier-facing behavior now works
6. what admin-facing approve/reject behavior now works
7. compatibility notes
8. postponed items

## Extra continuity note
This is Y2.1: supplier Telegram identity binding and onboarding gate.
It is not permission to implement supplier offer intake, supplier dashboard, supplier stats, supplier RFQ workspace, or broader auth/platform redesign in the same step.