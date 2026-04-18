Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- закрытия Track 5g.4a–5g.4e
- реализации Track 5g.5
- реализации Track 5g.5b
- hotfix supplier-offer deep-link `/start`
- реализации U1 — Mode 3 custom request customer experience
- реализации U2 — Mode 3 request lifecycle clarity
- реализации V1 — Mode 3 operational request handling
- реализации V2 — Mode 3 operational action clarity

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не расползайся в broad admin redesign, supplier redesign, payment redesign.

## Continuity base (обязательно принять)

Уже подтверждено:
- Layer A остаётся source of truth для booking/payment
- `TemporaryReservationService` — единственный hold path
- `PaymentEntryService` — единственный payment-start path
- Mini App остаётся thin delivery layer
- service layer владеет policy/business rules
- UI не дублирует backend rules

Уже закрыто:
- standalone catalog Mode 2 Mini App flow (5g.4a–5g.4e)
- context-specific CTA bridge into Mode 3 (5g.5)
- global always-available custom request entry (5g.5b)
- U1 — Mode 3 custom request customer experience
- U2 — Mode 3 request lifecycle clarity
- V1 — operational/admin read-side hints for custom requests
- V2 — operational/admin action clarity

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

After U1/U2/V1/V2:
- customer side for Mode 3 is much clearer
- operational side is much clearer
- but the transition chain between request -> selected response -> bridge -> customer action -> closed state can still be made more understandable

## Exact next safe step

Implement a medium-sized coherent block:

# V3 — Mode 3 Transition Visibility

### Goal
Make the transition path between custom request, commercial resolution, bridge state, and customer continuation easier to understand for internal/operational consumers, using only already existing architecture and states.

This is an operational/read-side visibility block.
Not a workflow redesign.
Not a payment block.
Not a bridge redesign.
Not a supplier model redesign.
Not a full admin-panel rewrite.

## Block scope

This block should include the following related pieces together.

### 1. Clarify request -> selected response visibility
Where internal/admin detail views already expose selected supplier response or commercial resolution context, make that relationship easier to interpret.

Examples:
- no selected response yet
- selected response exists
- selected response exists but no bridge yet
- selected response + bridge both exist
- request is closed/assisted/external/fulfilled without a customer continuation path

This should be visible without needing internal users to mentally reconstruct the whole lifecycle.

### 2. Clarify bridge presence and meaning
If a bridge exists, make it clearer what that means operationally:
- draft/prep-like state
- customer continuation available
- customer already has a next action
- bridge terminal / closed / replaced / superseded
- bridge exists historically but is no longer the active continuation path

Do not redesign the bridge.
Do not add new bridge lifecycle states unless absolutely necessary and narrowly justified.
Prefer better interpretation over new state machinery.

### 3. Clarify customer-action visibility from operational side
Operational/internal readers should more easily understand whether:
- customer has no next action yet
- customer-visible continuation exists
- customer should already be continuing through existing path
- the request is commercially resolved but waiting on customer
- the request is closed without customer continuation

This must not imply payment readiness unless that is truly supported by the existing flow.

### 4. Improve transition summary in detail responses
Add or improve a concise summary for operational detail responses that helps answer:
- where is this request in the transition chain?
- what relationship currently exists between resolution, bridge, and customer path?
- what is the next meaningful thing to monitor or do?

This should build on V1/V2 operational_hints instead of replacing them.

### 5. Keep list/detail distinction appropriate
Detail can be richer than list.
Do not overload list responses if the data is only truly useful in detail.
Keep list scan-friendly.

## What this block must NOT do

Do NOT:
- redesign supplier workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign full admin UI
- add a task/assignment engine
- add new major backend lifecycle states
- change Layer A semantics
- change Mode 2 hold/payment flow
- merge customer-facing and internal request semantics
- imply automatic next steps that do not actually exist

## Likely files/modules to touch

Only where needed:
- `app/services/operational_custom_request_hints.py`
- `app/schemas/custom_marketplace.py`
- `app/services/custom_marketplace_request_service.py`
- maybe tiny repository additions if needed for transition visibility
- focused tests for request/selection/bridge/customer-path interpretation

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier marketplace core logic
- Mini App booking/payment code
- unrelated private bot flows

## Required design guardrails

### A. Build on V1/V2, do not replace them
This should extend the already existing operational_hints model into clearer transition visibility.

### B. No fake transition states
Do not imply:
- payment can start if it cannot
- bridge is active if it is terminal/replaced
- customer already acted if there is no evidence
- supplier commitment that does not exist

### C. Keep it medium-sized and coherent
This is one operational package.
Do not smuggle in unrelated customer UX or backend redesign.

### D. Preserve current architecture
Do not redesign the marketplace.
Do not redesign the bridge.
Do not redesign admin surfaces broadly.

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit current V1/V2 hints and identify where transition meaning is still ambiguous
2. identify the useful truth already available from selected response + resolution + bridge presence/state
3. enrich detail-level transition visibility first
4. only add list-level transition signal if truly lightweight and useful
5. add focused tests
6. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only:
1. selected response / no selected response is interpreted more clearly
2. bridge presence/terminality/continuation meaning is clearer
3. customer-next-action visibility is not confused with payment readiness
4. terminal / resolved / customer-waiting states are not conflated
5. no fake continuation is implied

If a tiny internal read-side behavior cannot be cleanly unit-tested, keep changes minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what operational behavior is now improved
6. compatibility notes
7. postponed items

## Extra continuity note
This is the next medium-sized operational block after V1/V2.
It is not permission to redesign the broader marketplace, bridge, or payment architecture.