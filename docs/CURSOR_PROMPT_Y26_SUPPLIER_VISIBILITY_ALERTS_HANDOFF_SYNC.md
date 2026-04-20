Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2.3 supplier moderation/publication workspace implemented
- Y2.1a supplier legal/compliance hardening implemented
- Y24 supplier basic operational visibility implemented
- Y25 supplier narrow operational alerts implemented
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.
Не делать redesign.

## Goal
Synchronize continuity/handoff docs after Y24 and Y25 so the supplier subsystem state is accurately reflected.

## What must be reflected

### 1. Supplier subsystem current scope
Document that supplier v1 now includes:
- `/supplier` onboarding
- legal/compliance fields in onboarding for pending supplier approval
- `/supplier_offer` intake
- moderation/publication lifecycle
- retract path
- `/supplier_offers` narrow supplier workspace
- narrow operational visibility for supplier-owned offers
- narrow operational alerts

### 2. Current supplier read-side boundaries
Document clearly that supplier read-side currently includes:
- own offers only
- statuses
- reject reason visibility
- publication/retraction visibility
- basic narrow operational visibility
- narrow alerts such as:
  - publication retracted
  - departing soon
  - departed

### 3. Current supplier read-side limitations
Document clearly that supplier does NOT currently get:
- customer PII
- customer list
- payment rows/provider details
- booking/payment controls
- finance dashboard
- booking-derived aggregate alerts unless explicit authoritative linkage exists

### 4. Y24/Y25 truth
Document that Y24/Y25 intentionally remain read-side only and do not add new mutation/control surfaces.

### 5. Booking-derived alerting still postponed
Document that alerts like:
- first confirmed booking
- low remaining capacity
- sold out

remain postponed until there is an explicit safe and authoritative offer→execution linkage.

### 6. Next safe step
Set next safe step to something like:
- supplier-side richer read-only operational visibility / safe linkage design
OR
- narrow design gate for authoritative offer→execution linkage

Prefer the safer wording if current linkage is not yet explicit.

### 7. Boundaries still preserved
Reinforce:
- no Layer A booking/payment redesign
- no RFQ/bridge redesign
- no payment-entry/reconciliation redesign
- no supplier dashboard/analytics expansion yet
- no full RBAC/org redesign

## Files to update
Prefer only:
- `docs/CHAT_HANDOFF.md`
- optionally `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` if narrowly justified

Do not mass-edit historical prompts.

## Before coding
Output briefly:
1. current continuity state
2. why sync is needed
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
Do not implement the next feature in this step.