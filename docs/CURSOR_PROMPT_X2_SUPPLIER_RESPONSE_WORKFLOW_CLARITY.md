Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- закрытия Track 5g.4a–5g.4e
- реализации Track 5g.5
- реализации Track 5g.5b
- hotfix supplier-offer deep-link `/start`
- реализации U1 — Mode 3 custom request customer experience
- реализации U2 — Mode 3 request lifecycle clarity
- реализации V1 — Mode 3 operational request handling
- реализации V2 — Mode 3 operational action clarity
- реализации V3 — Mode 3 transition visibility
- реализации V4 — Mode 3 follow-through visibility
- реализации W1 — request lifecycle message preparation
- реализации W2 — request activity / message preview
- реализации W3 — internal/manual prepared request message surface
- реализации X1 — supplier-side request handling clarity

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не расползайся в broad supplier redesign, admin redesign, payment redesign.

## Continuity base (обязательно принять)

Уже подтверждено:
- Layer A остаётся source of truth для booking/payment
- `TemporaryReservationService` — единственный hold path
- `PaymentEntryService` — единственный payment-start path
- service layer владеет policy/business rules
- UI не дублирует backend rules

Уже укреплены:
- customer-side Mode 3
- admin/ops-side Mode 3
- request lifecycle messaging previews
- supplier-side request readability (X1)

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

После X1 supplier now understands the request better.
Следующий логичный supplier block:
сделать понятнее **собственный response workflow поставщика** без изменения правил.

## Exact next safe step

Implement a medium-sized coherent block:

# X2 — Supplier Response Workflow Clarity

### Goal
Make supplier-side response workflow easier to understand and act on by clarifying response state, editability, selected-state meaning, and “what happens next,” without redesigning supplier response rules.

This is a supplier-facing read/usability block.
Not a supplier workflow redesign.
Not a bridge redesign.
Not a payment block.
Not a full supplier portal rewrite.

## Block scope

### 1. Clarify supplier’s own response context
Where supplier sees a custom request detail, make it easier to understand:
- whether supplier already responded
- what kind of response they submitted
- whether they can still update it
- whether their response was selected
- whether the request moved beyond supplier action

This should be very obvious without reading raw fields.

### 2. Improve meaning of response states
Make supplier-facing wording clearer for states like:
- no response yet
- response submitted
- response updated
- declined
- proposed
- selected
- request under review
- request no longer actionable / closed

Use supplier-safe wording.
Do not leak admin-only semantics.

### 3. Clarify editability vs read-only
Supplier should more clearly understand whether they can:
- submit a new response
- update their existing response
- no longer change anything
- only view historical context

Do not change the actual rules.
Only make current rules easier to see.

### 4. Clarify “what happens next” for supplier
Supplier detail should better explain:
- if they still need to respond
- if they should wait
- if customer/platform review is in progress
- if their response was selected and supplier action is effectively done
- if request is closed and no more supplier action is expected

Do not promise booking/payment/commercial results beyond existing truth.

### 5. Keep request readability and response readability consistent
X1 improved request-side clarity.
X2 should complement that by improving response-side clarity, so supplier sees:
- what the request is
- what they did or did not do
- what happens next

## What this block must NOT do

Do NOT:
- redesign supplier response rules
- redesign commercial resolution model
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign full supplier portal
- add new major backend lifecycle states
- change Layer A semantics
- change Mode 2 hold/payment flow
- expose admin-only internal hints verbatim
- introduce a new permissions model unless absolutely necessary and tightly scoped

## Likely files/modules to touch

Only where needed:
- supplier-facing response/read helpers
- `app/schemas/custom_marketplace.py`
- `app/services/custom_marketplace_request_service.py`
- maybe the supplier hint builder added in X1
- focused tests for supplier response workflow clarity

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- admin-only operational hint logic except for safe adapted reuse
- Mini App booking/payment code
- unrelated private bot flows

## Required design guardrails

### A. Keep supplier semantics supplier-safe
Supplier should understand their own workflow, not internal platform triage jargon.

### B. No fake actionability
Do not imply supplier can update/respond when rules say they cannot.
Do not imply booking/payment/commercial rights that do not exist.

### C. Keep it medium-sized and coherent
This is one supplier-facing workflow-clarity block.
Do not smuggle in admin redesign or backend redesign.

### D. Preserve existing architecture
Do not redesign the marketplace or supplier lifecycle.

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit current supplier detail/list outputs after X1
2. identify biggest gaps around supplier’s own response context
3. improve response-state readability
4. improve editability/read-only clarity
5. improve “what happens next” wording
6. add focused tests
7. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only:
1. supplier can clearly see whether they responded or not
2. proposed/declined/selected meaning becomes clearer
3. editable vs read-only states are easier to interpret
4. selected/closed states are not confused with payment/booking outcomes
5. admin/internal semantics are not leaked directly

If a tiny supplier-facing read behavior cannot be cleanly unit-tested, keep changes minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what supplier-facing behavior is now improved
6. compatibility notes
7. postponed items

## Extra continuity note
This is X2: supplier response workflow clarity.
It is not permission to redesign the broader supplier workflow, bridge, or payment architecture.