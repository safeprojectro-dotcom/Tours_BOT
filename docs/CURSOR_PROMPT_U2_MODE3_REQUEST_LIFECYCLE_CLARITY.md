Продолжаем ЭТОТ ЖЕ проект Tours_BOT как strict continuation после:
- закрытия Track 5g.4a–5g.4e
- реализации Track 5g.5
- реализации Track 5g.5b
- hotfix supplier-offer deep-link `/start`
- реализации U1 — Mode 3 custom request customer experience block

Не начинай заново.
Не переоткрывай архитектуру.
Не трогай booking/payment core.
Не смешивай Mode 2 и Mode 3.
Не меняй RFQ/bridge execution semantics.
Не меняй payment-entry / reconciliation semantics.
Не расползайся в admin/operator/payment redesign.

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
- context-specific CTA bridge from unsuitable Mode 2 situations into existing Mode 3 custom request flow (5g.5)
- global always-available custom request entry across Mini App shell/navigation (5g.5b)
- U1 — Mode 3 / Custom Request Customer Experience:
  - safe prefill from context
  - clearer form UX
  - better post-submit success state
  - friendlier My Requests wording baseline

Текущее product truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

After U1, Mode 3 entry/submission is better, but the next medium-sized gap is:
- request lifecycle clarity for the customer after submission
- clearer status semantics
- better next-step understanding in My Requests / request detail

## Exact next safe step

Implement a medium-sized coherent block:

# U2 — Mode 3 / Request Lifecycle Clarity

### Goal
Make the customer-facing lifecycle of custom requests clearer and more actionable in Mini App, without redesigning backend RFQ/bridge architecture.

This is a customer read-side / UX clarity block.
Not a supplier workflow redesign.
Not a payment redesign.
Not a bridge redesign.
Not an admin redesign.

## Block scope

This block should include the following related pieces together.

### 1. Improve customer-facing request status semantics
Current raw/internal request states may exist in backend/service responses, but customer-facing Mini App wording should be clearer and more human-readable.

The customer should be able to understand states such as:
- request sent / received
- under review
- waiting for offers / responses
- offers available / next action available
- selected / moving forward
- closed / completed / unavailable

Use customer language, not internal system vocabulary where possible.

Do not expose raw internal status language if a clearer customer-facing phrase exists.

### 2. Improve request detail “what happens next” clarity
Request detail should more clearly communicate:
- what has already happened
- what the platform/team is doing now
- what the user can do next, if anything
- when the user should wait vs act

Add human-readable next-step guidance where safe.

Do not invent promises.
Do not imply a supplier already accepted if not true.
Do not imply booking/payment exists if not true.

### 3. Strengthen visibility of actionable continuation when it exists
If a request detail already has meaningful next action available through the existing architecture, make that continuation more visible and understandable.

Examples:
- if an offer/selection/bridge continuation already exists in current implemented flows, surface it clearly
- if no action exists yet, say that clearly rather than pretending the next step is hidden somewhere

This is not permission to redesign the bridge or payment path.
It is only about clearer customer-facing visibility of already-existing next actions.

### 4. Improve My Requests list grouping / empty / mixed state readability
My Requests should better explain states such as:
- no requests yet
- only active requests
- only closed requests
- a mix of active and closed requests
- requests that are waiting
- requests where a next action is available

Keep this lightweight and user-facing.

### 5. Add light expectation-setting copy where useful
Where safe, clarify user expectations:
- the team/platform is reviewing the request
- the user should check My Requests for updates
- the user will see the next action there when available

This is copy/read-side only.
Do not implement real notification workers in this block.

## What this block must NOT do

Do NOT:
- redesign supplier workflow
- redesign admin handling
- redesign RFQ response model
- redesign bridge/payment eligibility
- redesign payment architecture
- add new backend lifecycle states unless absolutely necessary and narrowly justified
- merge custom request with waitlist
- merge Mode 2 and Mode 3
- invent automated notifications that do not exist
- add operator workflow redesign

## Likely files/modules to touch

Only where needed:
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- existing My Requests / request detail Flet screens
- maybe tiny read-side formatting helpers / adapters
- focused tests for customer-facing lifecycle/status wording

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services
- supplier marketplace core services
- admin flows
- payment code
- unrelated private bot flows

## Required design guardrails

### A. Preserve Mode 3 as request lifecycle, not booking lifecycle
Do not blur the difference between:
- a request under review
- a reservation/order
- a payment-ready booking

### B. No fake promises
Do not say:
- “payment now” unless that action already exists
- “supplier confirmed” unless the system truly has that state
- “operator contacted” unless implemented
- “you will definitely be notified” unless existing behavior truly supports that wording

Use softer expectation-setting when needed.

### C. Keep UI thin
If any status-label mapping helper is needed, keep it read-side and narrow.
Do not move business logic into UI.

### D. Keep this a medium-sized block
This block is about lifecycle clarity for the customer.
Do not smuggle in unrelated supplier/admin/payment work.

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit current My Requests list/detail customer-visible wording
2. identify current internal/request states that are too raw or unclear
3. improve user-facing status labels and next-step copy
4. improve empty/mixed/list-level readability
5. improve request detail next-step clarity
6. surface existing actionable continuation more clearly when already present
7. add focused tests
8. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only for this block:
1. customer-facing request status wording is human-readable
2. request detail next-step copy does not promise nonexistent actions
3. My Requests empty/mixed states are clearer
4. already-existing actionable continuation is surfaced clearly when present
5. request lifecycle wording does not regress into booking/payment wording by mistake

If some Flet UI behavior cannot be cleanly unit-tested, keep the changes minimal and explain.

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
This is the next medium-sized customer-experience block for Mode 3 after U1.
It is not permission to redesign the broader marketplace, supplier operations, or payment architecture.