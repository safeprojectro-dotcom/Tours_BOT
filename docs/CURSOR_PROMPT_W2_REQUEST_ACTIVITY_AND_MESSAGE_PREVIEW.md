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

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

W1 created a safe message-preparation layer, but there is still almost no user-visible surface for it.
The next logical block should make request lifecycle messaging visible without pretending delivery already exists.

## Exact next safe step

Implement a medium-sized coherent block:

# W2 — Request Activity And Message Preview

### Goal
Add a user-visible request activity / latest-message preview layer in Mini App for Mode 3, using W1 prepared lifecycle messages, without introducing a real notification delivery engine.

This is a customer-facing read/UI block.
Not a delivery engine block.
Not a scheduler block.
Not a bridge redesign.
Not a payment redesign.

## Block scope

### 1. Add request activity / latest lifecycle message visibility
In `My Requests` and/or request detail, surface a safe user-visible lifecycle message preview derived from existing request state and W1 message preparation.

Examples:
- request recorded
- under review
- next step may exist
- closed

Important:
- this is a **preview/read surface**
- do not pretend a push/Telegram notification was sent
- do not claim real-time delivery

### 2. Improve request detail with a message/activity section
Add a lightweight section such as:
- latest update
- request activity
- what we told / would tell you now
- current request update

This should use W1-prepared message text or a closely related read-side view.
Keep it simple and human-readable.

### 3. Optionally add list-level preview if lightweight
If safe and not noisy, show a short latest-update preview in `My Requests` list.
Do not overload the list.
Prefer richer detail view if needed.

### 4. Keep wording fact-bound
Do not imply:
- booking exists
- payment is ready unless real
- supplier accepted unless real
- delivery was sent
- operator contacted unless implemented

If needed, use wording like:
- “Current update”
- “Latest request status”
- “What happens next”

### 5. Reuse W1 preparation safely
Prefer using the existing W1 message preparation layer or a thin read adapter around it.
Do not duplicate the same lifecycle copy in multiple places without reason.

## What this block must NOT do

Do NOT:
- implement real notification dispatch
- enqueue to outbox
- add scheduler/workers
- redesign supplier workflow
- redesign bridge/payment eligibility
- redesign payment architecture
- add new backend lifecycle states
- merge request messages with booking/payment notifications
- change Layer A semantics

## Likely files/modules to touch

Only where needed:
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- a thin adapter/helper calling W1 preparation safely for current request state
- maybe tiny read-side helpers for request detail/list
- focused tests for activity/message preview rendering

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier marketplace core logic
- full notification delivery engine
- unrelated private bot flows

## Required design guardrails

### A. Build on W1, don’t bypass it
Use W1-prepared request lifecycle message logic where safe.
Do not create a second inconsistent lifecycle copy system.

### B. No fake delivery
Never imply:
- “we sent you a notification”
- “you were notified”
- “push sent”
unless that is truly implemented

### C. Keep it medium-sized and coherent
This is one visible messaging/activity block.
Do not smuggle in delivery infrastructure or unrelated UI redesign.

### D. Preserve separation of domains
Mode 3 request activity is not the same as Layer A booking/payment notifications.

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit `My Requests` / request detail current UI
2. identify the smallest useful surface for latest update visibility
3. add a thin read adapter using W1 preparation
4. add detail-level activity/latest-update section first
5. add list-level preview only if lightweight and clearly useful
6. add focused tests
7. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only:
1. request detail can show safe current lifecycle message preview
2. preview does not imply delivery
3. next-action-related messaging does not imply booking/payment unless true
4. list/detail wording stays human-readable
5. existing Mode 3 customer semantics are not regressed

If some Flet UI behavior cannot be cleanly unit-tested, keep the change minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what user-visible behavior is now supported
6. compatibility notes
7. postponed items

## Extra continuity note
This is W2: visible request activity/message preview on top of W1 preparation.
It is not permission to build a real delivery engine yet.