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
- W1 request lifecycle message preparation
- W2 visible request activity/message preview

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

После W1/W2:
- у нас есть preparation layer
- есть customer-visible preview
- но пока нет хороших internal/manual action surfaces для использования prepared request messages без real delivery engine

## Exact next safe step

Implement a medium-sized coherent block:

# W3 — Request Message Action Surfaces

### Goal
Add safe manual/internal action surfaces for Mode 3 prepared lifecycle messages, so that internal/admin users can inspect and intentionally use request lifecycle messaging without pretending automated delivery already exists.

This is a messaging/admin-surface block.
Not a delivery-engine block.
Not a scheduler block.
Not a payment block.
Not a bridge redesign.
Not a supplier workflow redesign.

## Block scope

### 1. Add internal/manual preview surface for prepared request messages
Provide a safe way for internal/admin-facing request detail handling to expose:
- current prepared customer-facing request message
- message title/body
- event type / preview scope
- clear indication that this is prepared messaging, not proof of delivery

This can be an API/admin read surface, a detail-side enriched field, or another narrow internal surface consistent with the current architecture.

### 2. Add explicit “prepared, not sent” semantics
Wherever the prepared message is exposed internally, it must be unmistakable that:
- this is only a prepared message preview
- no outbox enqueue has happened
- no push/Telegram/customer delivery has happened
- this does not prove customer read/receipt

This is critical.

### 3. Make the prepared message operationally useful
The internal/admin user should be able to understand:
- what message the system would currently show/prepare for this request
- why that message is the current one
- whether it corresponds to request recorded / under review / next action may exist / closed / selection recorded

This should reuse W1/W2 logic, not fork it.

### 4. Keep customer/internal surfaces separate
This block is not about showing more delivery claims to the customer.
It is about giving internal users a reliable prepared-message surface based on existing truth.

### 5. Optionally expose lightweight metadata for future manual workflows
If useful, include safe metadata such as:
- event type
- preparation scope
- in_app_preview_only
- maybe language used
- maybe a note like “manual review only”

Only if clearly helpful and safe.

## What this block must NOT do

Do NOT:
- implement real delivery
- enqueue to outbox
- add scheduler/workers
- redesign notification engine
- redesign supplier workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- add new backend lifecycle states
- imply sent/read/delivered semantics
- change Layer A semantics

## Likely files/modules to touch

Only where needed:
- `app/services/custom_request_notification_preparation.py`
- maybe a thin adapter/service for internal prepared-message exposure
- `app/schemas/custom_marketplace.py`
- `app/services/custom_marketplace_request_service.py`
- possibly admin-facing request detail read surface
- focused tests for prepared-message action surface

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- full notification delivery engine
- unrelated private bot flows
- Mini App booking/payment code

## Required design guardrails

### A. Build on W1/W2, don’t duplicate messaging logic
Use the same preparation truth as W1/W2 where safe.

### B. No fake delivery
Never imply:
- “sent”
- “delivered”
- “notified”
- “customer received”
unless that is truly implemented

### C. Keep it medium-sized and coherent
This is one manual/internal messaging-surface block.
Do not smuggle in delivery infrastructure or unrelated UI redesign.

### D. Preserve domain separation
Mode 3 request prepared messages are not Layer A booking/payment notifications.

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit W1/W2 and identify the cleanest internal surface
2. add a prepared-message read structure for internal/admin use
3. wire it into the relevant request detail path
4. make “prepared not sent” explicit in schema/copy
5. add focused tests
6. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only:
1. internal prepared message surface returns safe current message preview
2. preview explicitly does not imply delivery
3. event type/preparation scope stay consistent with W1
4. customer-facing behavior is not unintentionally changed
5. no booking/payment semantics leak into request messaging

If a tiny internal read-side behavior cannot be cleanly unit-tested, keep changes minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what internal/manual messaging behavior is now supported
6. compatibility notes
7. postponed items

## Extra continuity note
This is W3: manual/internal action surfaces for prepared request lifecycle messages.
It is not permission to build a real delivery engine yet.