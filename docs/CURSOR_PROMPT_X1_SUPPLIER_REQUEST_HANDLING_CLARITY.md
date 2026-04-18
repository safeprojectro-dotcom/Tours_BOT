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

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не расползайся в broad admin redesign, payment redesign, marketplace redesign.

## Continuity base (обязательно принять)

Уже подтверждено:
- Layer A остаётся source of truth для booking/payment
- `TemporaryReservationService` — единственный hold path
- `PaymentEntryService` — единственный payment-start path
- service layer владеет policy/business rules
- UI не дублирует backend rules

Уже сильно укреплены:
- customer-side Mode 3
- admin/ops-side Mode 3
- request lifecycle messaging preparation and previews

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

Следующий самый логичный домен:
улучшить **supplier-side usability** для обработки custom requests, не меняя core semantics.

## Exact next safe step

Implement a medium-sized coherent block:

# X1 — Supplier Request Handling Clarity

### Goal
Make supplier-side custom request handling clearer and easier to act on, using the already existing request marketplace architecture, without redesigning supplier workflow or RFQ semantics.

This is a supplier-facing read/usability block.
Not a supplier model redesign.
Not a bridge redesign.
Not a payment block.
Not a full supplier portal rewrite.

## Block scope

### 1. Improve supplier list readability for custom requests
Where suppliers see custom requests, make the list easier to scan:
- what the request is about
- whether it is still actionable
- whether supplier already responded
- whether request appears closed / no longer actionable
- basic route/date/group summary where available

Keep it concise and supplier-useful.

### 2. Improve supplier detail readability
Supplier detail view should make it easier to understand:
- request summary
- what customer seems to need
- current actionable state for supplier
- whether supplier can still respond or not
- whether request has already moved beyond supplier action

Do not expose internal/admin-only semantics unnecessarily.

### 3. Clarify supplier action availability
Make it clearer when supplier can:
- submit/update response
- no longer act
- only view historical context
- see that request is already commercially progressed beyond supplier action

This is visibility/clarity only.
Do not redesign supplier response rules.

### 4. Improve distinction between:
- open and actionable
- open but already responded
- under review / limited supplier action
- no longer actionable / closed
- historical visibility only

Keep this supplier-facing and understandable.

### 5. Preserve separation from admin-only/internal hints
Do not leak V1–V4 internal operational semantics directly into supplier responses.
Supplier side should get its own safe, simpler wording.

## What this block must NOT do

Do NOT:
- redesign supplier workflow
- redesign commercial resolution model
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign full supplier portal
- add new major backend lifecycle states
- change Layer A semantics
- change Mode 2 hold/payment flow
- expose admin-only operational hints verbatim
- introduce new permissions model unless absolutely necessary and tightly scoped

## Likely files/modules to touch

Only where needed:
- supplier-facing custom request list/detail read helpers
- `app/schemas/custom_marketplace.py`
- `app/services/custom_marketplace_request_service.py`
- maybe a small supplier-facing hint helper/service
- focused tests for supplier-facing clarity

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- admin-only operational hint logic except for safe reuse behind translation/adaptation
- Mini App booking/payment code
- unrelated private bot flows

## Required design guardrails

### A. Keep supplier semantics supplier-safe
Supplier should see:
- what matters for responding
- what no longer needs their action
- what they already did
Not admin-only internal triage language.

### B. No fake actionability
Do not imply supplier can still act when request is closed or no longer actionable.
Do not imply commercial selection/booking rights that do not exist.

### C. Keep it medium-sized and coherent
This is one supplier-facing readability/action-clarity block.
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

1. audit current supplier custom-request list/detail outputs
2. identify biggest clarity/actionability gaps
3. improve list-level readability
4. improve detail-level readability and actionability cues
5. improve “already responded / still actionable / no longer actionable” clarity
6. add focused tests
7. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only:
1. supplier-facing list/detail wording becomes clearer
2. supplier actionability is easier to interpret
3. already-responded vs still-actionable vs closed is not confused
4. admin-only/internal semantics are not leaked directly
5. no bridge/payment semantics are implied incorrectly

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
This is X1: supplier-side request handling clarity.
It is not permission to redesign the broader supplier workflow, bridge, or payment architecture.