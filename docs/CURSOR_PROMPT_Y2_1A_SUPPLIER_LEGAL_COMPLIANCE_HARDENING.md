Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2 design gate accepted
- Y2.1 supplier onboarding live-verified
- Y2.2 supplier Telegram offer intake live-verified
- Y2.2a intake polish/navigation/validation live-smoke verified
- Y2.3 supplier moderation/publication workspace implemented
- current updated `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment core.
Не менять RFQ/bridge execution semantics.
Не менять payment-entry/reconciliation semantics.
Не делать broad redesign supplier/admin platform.

## Problem
Supplier operational loop now exists, but supplier onboarding is still legally/compliance-light.
This creates risk:
- a supplier may become operationally approved without sufficient legal business identity data
- this is dangerous for transport/tourism compliance

## Goal
Harden supplier onboarding and approval with mandatory legal/compliance identity fields, while preserving the current narrow supplier v1 operating model.

This is a scoped supplier compliance hardening step.
Not a broad KYC platform.
Not a full legal-document system.
Not a broad auth redesign.

## Continuity base
Use as source of truth:
- current codebase
- `docs/CHAT_HANDOFF.md`
- `docs/SUPPLIER_TELEGRAM_OPERATING_MODEL_Y2.md`

Already true:
- supplier v1 = one supplier + one primary Telegram operator
- `/supplier` onboarding exists
- admin approve/reject gate exists
- supplier offer flow exists
- moderation/publication workspace exists

## Exact next safe step
# Y2.1a — Supplier legal/compliance hardening

## What this step must decide/implement
Supplier onboarding must require and persist the minimum legal identity fields needed for safer supplier approval, such as:
- legal entity type (company / individual entrepreneur / allowed category)
- legal registered name
- CUI / registration code
- permit/license type
- permit/license number

Optionally, if still narrow and safe:
- issuing authority
- country/jurisdiction
- expiry date

But avoid overbuilding.

## Implementation goals

### 1. Extend supplier onboarding FSM
Add the required legal/compliance fields into `/supplier` onboarding in a supplier-friendly way.

### 2. Persist legal identity fields in supplier domain
Use a proper persistence model in the supplier domain.
Do not leave critical legal identity only in ephemeral Telegram text.

### 3. Tighten admin approval meaning
Admin approve should now mean:
- operational approval after reviewing both operational and legal identity fields

If needed, refine admin read-side visibility so admin can actually see the legal fields they are approving.

### 4. Keep model narrow
Do not build document upload workflows, legal audit systems, or broad compliance dashboards in this step unless absolutely necessary.

### 5. Preserve current supplier loop
Do not break:
- existing approved suppliers unnecessarily without a migration plan
- supplier offer draft/moderation lifecycle
- publication flow

If existing suppliers need backward-compatible handling, do it conservatively and explicitly.

## What this step must NOT do
Do NOT:
- redesign supplier organization/RBAC
- build full KYC/document storage platform
- redesign moderation/publication workflow
- redesign booking/payment/RFQ semantics
- build analytics/dashboard
- create broad admin portal rewrite

## Likely files to touch
Likely:
- supplier model/schema/service
- `/supplier` onboarding FSM/messages
- admin supplier read/write visibility if needed
- migration if legal fields need new columns
- focused tests

## Before coding
Output briefly:
1. current project state
2. why legal/compliance hardening is the next priority
3. exact legal fields proposed
4. likely files to change
5. risks
6. what remains postponed

## Suggested implementation order
1. inspect current supplier model and onboarding fields
2. decide minimum required legal identity fields
3. add persistence model + migration if needed
4. extend onboarding FSM
5. expose legal fields to admin review
6. preserve backward compatibility safely
7. add focused tests

## Required focused tests
Add focused tests for:
1. onboarding requires the new legal fields
2. legal identity fields persist correctly
3. admin can see/review them
4. supplier approval semantics stay coherent
5. no booking/payment/RFQ semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier-facing onboarding now requires
6. what admin approval now sees/uses
7. compatibility notes
8. postponed items

## Important note
This is a narrow compliance-hardening step.
Do not silently expand into document workflows, analytics, broad supplier portal redesign, or auth/RBAC redesign.