Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2.3 supplier moderation/publication workspace implemented
- Y2.1a supplier legal/compliance hardening implemented
- Railway production migration applied through `20260426_15`
- current codebase and current `docs/CHAT_HANDOFF.md`

Это documentation-only sync step.
Не писать runtime code.
Не менять migrations.
Не менять tests.
Не делать UI/backend redesign.

## Goal
Synchronize continuity/handoff docs after:
- Y2.3
- Y2.1a

## Current accepted truth that must be reflected

### 1. Supplier v1 operating loop now exists
Document that the supplier subsystem now includes:
- `/supplier` onboarding entry
- onboarding statuses: `pending_review` / `approved` / `rejected`
- admin approve/reject gate
- `/supplier_offer` intake
- offer draft persistence
- explicit submit to `ready_for_moderation`
- admin approve / reject / publish
- retract path for published offers
- `/supplier_offers` supplier read-side visibility
- supplier Telegram notifications on:
  - approved
  - rejected with reason
  - published
  - retracted

### 2. Approve vs publish decision
Document clearly:
- approve does NOT auto-publish
- publish is a separate admin action
- reject includes supplier-visible reason
- retract returns published offer to approved
- Telegram channel deletion on retract is best-effort

### 3. Supplier legal/compliance hardening
Document that supplier onboarding now requires legal/compliance identity fields for the pending supplier approval path:
- `legal_entity_type`
- `legal_registered_name`
- `legal_registration_code`
- `permit_license_type`
- `permit_license_number`

Document that admin approve for pending supplier now requires legal completeness.

### 4. Backward-compatibility truth
Document explicitly and honestly:
- legacy already-approved suppliers remain backward-compatible
- existing approved supplier rows may still have `NULL` in the new legal fields
- this is by design of the narrow compatibility model
- the legal completeness guard applies to approving pending suppliers, not retroactive forced migration of already-approved suppliers

### 5. What is live-verified vs not fully live-verified
Document carefully:
- Y2.3 moderation/publication workspace is implemented
- Railway migration for Y2.1a is applied and production schema is current
- supplier offer flow remains live-working for existing approved supplier
- legacy approved supplier behavior is confirmed
- full clean-room live verification of a brand-new supplier going through the new legal onboarding path is still pending

Do not overclaim.

### 6. Boundaries still preserved
Reinforce:
- no Layer A booking/payment semantics change
- no RFQ/bridge semantics change
- no payment-entry/reconciliation semantics change
- no Mode 2 / Mode 3 merge
- no broad supplier/admin portal redesign
- no broad RBAC/org redesign

### 7. Current supplier read-side scope
Document that supplier read-side is still narrow:
- own offers
- statuses
- reject reason visibility
- publication/retraction notifications
- no customer PII
- no analytics/dashboard yet
- no booking/payment controls

### 8. Next safe step
Set next safe step to:
- narrow supplier operational visibility / basic stats

Meaning:
- basic published-offer operational visibility
- load/seat progress style metrics only when safe
- no customer PII
- no finance dashboard
- no booking/payment control redesign

### 9. Do not reopen by default
Do not reopen by default:
- legal document upload / KYC file workflows
- full audit/compliance subsystem
- analytics portal rewrite
- full supplier organization/RBAC redesign
- RFQ redesign
- booking/payment redesign

## Files to update
Prefer only:
- `docs/CHAT_HANDOFF.md`
- optionally `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` if narrowly justified

Do not mass-edit historical prompt docs.

## Before coding
Output briefly:
1. current continuity state
2. why sync is needed now
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