Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- Y30 design accepted
- Y30.1 stable Mini App published supplier-offer landing implemented
- Y30.2 supplier-offer actionability resolver implemented
- Y30.3 supplier-offer landing execution activation contract implemented
- Y30.3 handoff sync completed
- current `docs/CHAT_HANDOFF.md`

Не начинать заново.
Не переоткрывать архитектуру.
Не менять Layer A booking/payment semantics.
Не менять RFQ/bridge semantics.
Не сливать `supplier_offers` и `tours`.
Не делать broad publication redesign.

## Goal
Implement the next narrow operational step:

**supplier-offer execution linkage workflow / linkage operations**

The system already supports:
- published supplier-offer channel visibility
- stable Mini App landing
- actionability evaluation
- execution activation only when authoritative linkage exists

But operationally, `supplier_offer_execution_links` is still empty.
This step must make it possible to explicitly create/manage the linkage so scenario A becomes реально testable.

## Accepted design truth
- `supplier_offer` remains commercial/showcase/publication object
- `tour` remains Layer A execution/catalog object
- direct execution is allowed only through explicit authoritative linkage
- no uncontrolled auto-mapping
- visibility != bookability

## Exact scope

### 1. Explicit linkage workflow
Implement the narrowest safe operational workflow to create and manage `supplier_offer_execution_links`.

At minimum support:
- explicit create link for published supplier offer -> existing tour
- one active link per offer preserved
- replace/close semantics preserved if already defined in linkage subsystem

### 2. Reuse existing linkage truth
Reuse the existing linkage model and invariants already present in the project.
Do not redesign the schema if the current linkage table/service already exists and is sufficient.

### 3. Operational surface
Expose linkage operations through the narrowest already-accepted operational/admin surface.

Preferred:
- existing admin API path(s), if already present but incomplete for current workflow
- or the smallest admin operational path needed to create the link

Do NOT build a broad new portal/workspace in this step.

### 4. Safe constraints
Linking must be allowed only when safe and explicit.
At minimum:
- supplier offer must be in appropriate published/operationally visible state
- target tour must exist
- invalid combinations must return explicit errors
- no fake linkage
- no silent replacement without preserving history if replace semantics exist

### 5. Minimal read visibility
Ensure operationally that once link exists:
- supplier-offer landing can resolve execution target when otherwise eligible
- scenario A becomes possible to test
No extra analytics/dashboard work.

### 6. No auto-create in this step
Do NOT implement:
- auto-create Layer A tour from supplier offer
- auto-suggest mapping logic
- coupon logic
- broad conversion workflow redesign
- broad admin UI redesign

## Expected behavior

### Case A
Admin/operator explicitly links published supplier offer to existing tour.
Then supplier-offer landing, when `bookable`, can expose direct execution CTA into existing Layer A flow.

### Case B
No link exists.
Landing remains safe fallback only.

### Case C
Link closed/replaced.
Landing stops using the old execution target.

## Likely files
Likely:
- existing linkage repository/service files
- admin API route(s)
- schema files for admin request/response if needed
- focused tests
Possibly small read-path confirmation if required, but avoid unrelated Mini App redesign.

## Before coding
Output briefly:
1. current state
2. why Y30.4 is the next safe step
3. likely files to change
4. risks
5. what remains postponed

## Required tests
Add/update focused tests for:
1. explicit link create for published supplier offer -> existing tour
2. invalid link attempt rejected safely
3. one-active-link invariant preserved
4. landing/execution activation can consume new linkage truth
5. no Layer A booking/payment semantics changed

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what operator/admin can now do
6. what user can now do from supplier-offer landing when link exists
7. what remains postponed
8. compatibility notes

## Important note
This is an explicit linkage workflow step only.
Do not silently implement auto-create tour, auto-mapping, coupon logic, or broad conversion redesign.