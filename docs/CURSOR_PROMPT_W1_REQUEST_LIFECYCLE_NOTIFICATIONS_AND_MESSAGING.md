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
- U1/U2 customer-side Mode 3 clarity
- V1/V2/V3/V4 operational/admin-side Mode 3 clarity

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

Сейчас customer side и operational side у Mode 3 уже сильно укреплены.
Следующий логичный домен — **request lifecycle notifications and messaging**, чтобы после создания и движения запроса пользователь и система имели более цельную messaging layer.

---

## Exact next safe step

Implement a medium-sized coherent block:

# W1 — Request Lifecycle Notifications And Messaging

### Goal
Add a safe, explicit messaging/notification preparation layer for Mode 3 request lifecycle events, without redesigning the marketplace, booking core, or payment architecture.

This is a notification/messaging block.
Not a booking block.
Not a payment block.
Not a bridge redesign.
Not a supplier workflow redesign.
Not a full notification-platform rewrite.

---

## Block scope

This block should include the following related pieces together.

### 1. Define customer-facing request lifecycle message events
Introduce or extend a safe message-preparation layer for important Mode 3 lifecycle events such as:
- custom request created
- request updated / under review
- customer-visible next action available
- request closed / no further continuation
- maybe bridge/customer-continuation available, if and only if this is already truly supported by the existing architecture

Use only events that map to existing truth.
Do not invent lifecycle milestones that do not exist.

### 2. Keep messaging fact-bound
Every customer-facing message must remain accurate:
- do not claim payment is ready unless the system truly supports that next step
- do not claim a supplier accepted unless system truth supports it
- do not claim the request is booked
- do not claim an operator was assigned unless that is truly implemented
- do not promise push notifications or proactive delivery channels that do not yet exist

If this block prepares notification payloads but not delivery, state that clearly in architecture/code.

### 3. Reuse existing notification patterns where appropriate
The project already has notification preparation/dispatch foundations on Layer A.
Where safe, reuse existing patterns/conventions instead of inventing a parallel messaging architecture.

But:
- do not force-fit Mode 3 into Mode 2/Layer A booking semantics
- keep request lifecycle messaging clearly separate from reservation/payment notifications

### 4. Add customer-readable message copy for the main Mode 3 lifecycle points
The wording should reflect the improved customer journey already built in U1/U2:
- request submitted
- what happens next
- where to check status (`My Requests`)
- next action available, if real
- request closed, if applicable

Copy should stay concise, clear, and non-committal beyond existing truth.

### 5. Keep operational/customer messaging boundaries clear
If any internal-only lifecycle concept exists in V1–V4, do not leak it directly into customer-facing request notifications unless intentionally translated into safe customer wording.

---

## What this block must NOT do

Do NOT:
- redesign supplier workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign full notification delivery infra
- add real scheduler/orchestrator complexity unless already trivially supported
- add new backend lifecycle states unless absolutely necessary and tightly scoped
- merge request notifications with booking/payment notifications semantically
- imply real-time guaranteed delivery if not implemented
- change Layer A booking/payment semantics

---

## Likely files/modules to touch

Only where needed:
- request-lifecycle notification preparation service(s)
- existing notification preparation patterns/helpers
- message/translation string tables for request lifecycle copy
- maybe tiny schema additions for prepared payloads if needed
- focused tests for request lifecycle message preparation

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier marketplace core logic
- Mini App booking/payment code
- unrelated private bot flows
- full notification delivery engine unless already safely reusable

---

## Required design guardrails

### A. Build on existing notification foundation, don’t fork architecture
Prefer reuse of existing preparation patterns.
Do not create a second unrelated notification architecture without need.

### B. No fake messaging
Do not tell the customer:
- booking exists
- payment is ready
- supplier is confirmed
- action is urgent unless system truth supports it
- they will definitely be notified proactively unless that is actually implemented

### C. Keep this medium-sized and coherent
This is one messaging block for Mode 3 lifecycle.
Do not smuggle in unrelated customer UX or backend redesign.

### D. Preserve separation of domains
Mode 3 request messages are not the same as Mode 2 reservation/payment messages.

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

1. audit existing notification preparation foundation
2. identify which Mode 3 lifecycle events can be messaged safely today
3. add request-lifecycle message event/type definitions if needed
4. implement message preparation for the safe subset of events
5. add localized copy for en/ro at minimum
6. add focused tests
7. keep docs/continuity updates minimal unless truly needed

---

## Tests required

Add focused tests only:
1. request-created message preparation is correct and safe
2. request-next-action-available messaging does not imply booking/payment unless true
3. request-closed messaging is clear and non-misleading
4. customer-facing copy does not leak internal-only operational semantics
5. existing Layer A booking/payment notification semantics are not regressed if shared helpers are touched

If some delivery behavior is intentionally out of scope, make that explicit and test preparation only.

---

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what messaging/notification behavior is now supported
6. compatibility notes
7. postponed items

---

## Extra continuity note
This is the first W-block: Mode 3 request lifecycle notifications and messaging.
It is not permission to redesign the broader marketplace, notification engine, bridge, or payment architecture.