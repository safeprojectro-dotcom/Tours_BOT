Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- закрытия Track 5g.4a–5g.4e
- реализации Track 5g.5
- реализации Track 5g.5b
- hotfix supplier-offer deep-link `/start`
- реализации U1 — Mode 3 custom request customer experience
- реализации U2 — Mode 3 request lifecycle clarity
- реализации V1 — Mode 3 operational request handling

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

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

После V1 internal users can better understand what a request is.
The next practical medium block is to make it clearer **what internal users can actually do next** using the already existing architecture.

---

## Exact next safe step

Implement a medium-sized coherent block:

# V2 — Mode 3 Operational Action Clarity

### Goal
Make the next actionable step for operational/admin handling of custom requests clearer and more visible, using only already existing workflow/bridge/commercial resolution states.

This is an operational/readability/action-clarity block.
Not a new workflow engine.
Not a payment block.
Not a bridge redesign.
Not a supplier model redesign.
Not a full admin-panel rewrite.

---

## Block scope

This block should include the following related pieces together.

### 1. Clarify operational actionability in list/detail responses
Where internal/admin request list/detail data is returned, make it clearer whether the request is:
- waiting for review
- waiting for supplier/commercial progress
- ready for internal decision
- already has selected/bridge-related continuation
- already waiting on customer action
- already terminal / closed

This should build on top of V1 operational hints, not replace them.

### 2. Add clearer “what can be done now” visibility
For operational/internal consumers, surface clearer action-oriented hints such as:
- review supplier responses
- select/confirm commercial direction
- prepare or inspect bridge state
- monitor customer continuation
- no further action required / already closed

Use current system truth only.
Do not invent actions that are not supported by the existing architecture.

### 3. Make bridge/commercial continuation state easier to interpret
If a request already has:
- selected response
- commercial resolution
- booking bridge
- bridge closure/replacement/supersede state
- customer continuation path already available

then operational/detail responses should make that easier to understand at a glance.

This is visibility/clarity only.
Do not redesign bridge lifecycle.
Do not redesign payment eligibility.
Do not create new backend status models unless absolutely necessary and narrowly justified.

### 4. Improve distinction between:
- “request still needs operational work”
- “system/customer next action exists”
- “commercially resolved but still in progress”
- “fully terminal / nothing else to do”

This is one of the main goals of the block.

### 5. Keep internal semantics internal
These improvements are for admin/operational handling.
They must not leak into supplier/customer-facing semantics unless a tiny shared-helper fix is absolutely necessary.

---

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

---

## Likely files/modules to touch

Only where needed:
- `app/services/operational_custom_request_hints.py`
- `app/schemas/custom_marketplace.py`
- `app/services/custom_marketplace_request_service.py`
- maybe tiny repository additions if needed for existing-state visibility
- focused tests for operational action clarity

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier marketplace core logic
- Mini App booking/payment code
- unrelated private bot flows

---

## Required design guardrails

### A. Build on V1, do not replace it
This should extend V1 operational hints into stronger action clarity.
Do not restart from scratch.

### B. No fake actionability
Do not imply:
- payment can start if it cannot
- bridge is ready if it is not
- customer has already acted if they have not
- supplier selected state if none exists

### C. Keep it medium-sized and coherent
This is one operational package.
Do not smuggle in unrelated customer UX or backend redesign.

### D. Preserve current architecture
Do not redesign the marketplace.
Do not redesign the bridge.
Do not redesign admin surfaces broadly.

---

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

---

## Suggested implementation order

1. audit current V1 operational hints and remaining ambiguity
2. identify which existing states are still hard to act on
3. extend operational list/detail hints for actionability
4. improve bridge/commercial continuation visibility
5. improve distinction between “needs work”, “waiting on customer”, and “terminal”
6. add focused tests
7. keep docs/continuity updates minimal unless truly needed

---

## Tests required

Add focused tests only:
1. operational action hints are clearer and stable
2. existing bridge/commercial continuation states become easier to interpret
3. terminal vs active vs customer-waiting semantics are not confused
4. no fake payment/bridge readiness is implied
5. customer-facing semantics are not unintentionally regressed if shared helpers are touched

If a tiny internal read-side behavior cannot be cleanly unit-tested, keep changes minimal and explain.

---

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what operational behavior is now improved
6. compatibility notes
7. postponed items

---

## Extra continuity note
This is the next medium-sized operational block after V1.
It is not permission to redesign the broader marketplace, supplier operations model, or payment architecture.