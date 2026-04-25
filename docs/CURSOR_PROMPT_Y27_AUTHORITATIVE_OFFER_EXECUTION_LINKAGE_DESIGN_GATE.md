Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y2.3 supplier moderation/publication workspace implemented
- Y2.1a supplier legal/compliance hardening implemented
- Y24 supplier basic operational visibility implemented
- Y25 supplier narrow operational alerts implemented
- updated `docs/CHAT_HANDOFF.md`

Это design-only step.
Не писать runtime code.
Не менять migrations.
Не менять tests.
Не делать hidden implementation.
Нужен только design/decision output.

## Goal
Define a safe, explicit, authoritative design for supplier-offer-to-execution linkage, so future supplier operational visibility can use real execution truth without inventing fake booking math.

## Why this step exists
Current supplier alerts/visibility deliberately avoid booking-derived metrics because the project does not yet have a clean, authoritative linkage between:
- published supplier offers
and
- actual execution objects / customer-booking truth / Layer A order reality

Without that linkage, supplier-facing stats like:
- first confirmed booking
- low remaining seats
- sold out
- confirmed vs reserved
would be risky or misleading.

## Design problem to solve
We need to decide how a supplier-owned published offer can be safely linked to real execution truth, while preserving all existing architecture boundaries:
- no Layer A redesign
- no RFQ/bridge redesign
- no fake UI-only math
- no Mode 2/Mode 3 merge
- no broad portal rewrite

## Required output
Produce a narrow design recommendation covering:

### 1. What entity is the source of execution truth?
Clarify what future supplier booking-derived visibility should rely on:
- `Tour`
- `Order`
- existing booking facade
- another already-existing authoritative read model
- or a new narrow linkage record if truly required

### 2. What is the linkage object?
Explain how a supplier offer should map to execution truth:
- direct `supplier_offer -> tour`
- `supplier_offer -> published catalog object -> tour`
- one-to-many risk
- replacement/republication risk
- retract/publish edge cases
- whether linkage should be immutable or replaceable

### 3. What signals become safely derivable once linkage exists?
List exactly which supplier-facing aggregate metrics would then become safe, for example:
- confirmed count
- active reserved/hold count
- remaining seats
- sold out
- first booking signal
- low remaining threshold

Do not include any PII.

### 4. What remains unsafe even with linkage?
Be explicit about what supplier still should NOT see:
- customer identities
- payment rows/provider details
- admin-only internals
- RFQ-sensitive data beyond allowed surfaces
- finance/reporting beyond narrow aggregate operational truth

### 5. Interaction with current lifecycle
Explain how linkage interacts with:
- approved vs published
- retract/unpublish
- expired/departed offers
- edited/republished offers
- legacy offers already in DB

### 6. Migration vs no-migration recommendation
State clearly whether the cleanest safe path requires:
- no schema change
- additive schema change
- or only read-side convention

If migration is recommended, explain why narrowly.

### 7. Recommended next implementation step
Recommend the narrowest safe implementation step after this design gate.
For example:
- additive linkage field
- read model
- safe aggregate stats only
- booking-derived alerts only after linkage

## Constraints
Do NOT:
- redesign Layer A booking/payment core
- redesign RFQ/bridge semantics
- redesign payment-entry/reconciliation semantics
- merge supplier offers with RFQ/custom request model
- propose a huge analytics/data warehouse solution
- propose broad supplier dashboard rewrite
- propose customer PII exposure
- silently implement code in this step

## Inputs / source of truth
Use:
- current codebase
- current `docs/CHAT_HANDOFF.md`
- supplier offer lifecycle already implemented
- Y24/Y25 decisions
- existing Layer A booking/order truth

## Before coding
Output briefly:
1. current project state
2. why linkage design is needed now
3. what artifacts you will inspect
4. risks if we skip this design step

## After coding
Report exactly:
1. files changed
2. code changes none
3. migrations none
4. design recommendation summary
5. safest next implementation step
6. postponed items

## Preferred file(s)
Create/update only narrow docs, for example:
- `docs/SUPPLIER_OFFER_EXECUTION_LINKAGE_DESIGN.md`
- and minimal `docs/CHAT_HANDOFF.md` mention only if truly needed

## Important note
This is a design gate only.
Do not implement the linkage in this step.