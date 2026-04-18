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
- реализации X2 — supplier response workflow clarity

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
- service layer владеет policy/business rules
- UI не дублирует backend rules

Уже сильно укреплены:
- customer-side Mode 3
- admin/ops-side Mode 3 read models
- request lifecycle messaging previews
- supplier-side clarity

Текущее truth:
- Mode 2 = ready-made catalog full-bus offer
- Mode 3 = custom request / individual route / group request
- Mode 2 != Mode 3

На текущий момент backend/read-side для request marketplace уже стал богатым, но следующая логичная ценность — **дать admin-facing UI/visual operational surfaces**, чтобы все эти hints, statuses, transition/follow-through/messaging blocks были реально удобны в работе, а не существовали только в API/JSON.

## Exact next safe step

Implement a medium-sized coherent block:

# A1 — Admin UI / Operational Surfaces

### Goal
Surface the already-built operational clarity for Mode 3 custom requests into a more useful internal/admin-facing UI layer, without redesigning the admin architecture or changing workflow semantics.

This is an admin/internal UI/read block.
Not a payment block.
Not a bridge redesign.
Not a supplier model redesign.
Not a full admin-panel rewrite.

## Block scope

### 1. Improve admin list visual scanability
Where admins see custom requests in UI, make the list easier to scan visually using already-existing read-side truth:
- request summary
- stage / action focus
- whether internal attention is needed
- whether customer continuation exists or may exist
- whether request is terminal
- maybe latest prepared-message or update hint if lightweight and clearly useful

Keep the list useful and compact.

### 2. Improve admin detail visual structure
Request detail UI should surface existing rich read-side information in clearer sections, such as:
- request summary / essentials
- operational status / action hints
- transition visibility
- follow-through visibility
- prepared customer message preview
- bridge/commercial continuation context

The goal is not to invent new data, but to present current data better.

### 3. Make next-step/action blocks clearer
Admins should visually understand:
- what needs attention now
- what is waiting on supplier/commercial progression
- what is waiting on customer continuation
- what is already closed/terminal
- what prepared customer message currently exists

Use the already existing read-side hints, not new backend logic.

### 4. Keep customer/internal/supplier semantics separated in UI
Admin UI may be richer than supplier/customer wording, but it must not collapse all roles into one vocabulary.
Use internal-safe, human-readable wording.

### 5. Keep it additive and safe
Use already-existing schemas and operational/message fields wherever possible.
Do not redesign API contracts unless a tiny additive field is absolutely necessary.

## What this block must NOT do

Do NOT:
- redesign admin architecture broadly
- redesign bridge/payment eligibility
- redesign payment architecture
- redesign supplier workflow
- add new major backend lifecycle states
- change Layer A semantics
- change Mode 2 hold/payment flow
- merge supplier/customer/admin semantics
- invent new workflow actions that do not exist

## Likely files/modules to touch

Only where needed:
- admin-facing UI files/screens/templates/components
- maybe tiny UI-specific adapters/formatters
- maybe minimal additive read helpers if absolutely needed
- focused tests for admin UI/readability if feasible

Avoid touching unless absolutely necessary:
- `TemporaryReservationService`
- `PaymentEntryService`
- `PaymentReconciliationService`
- RFQ bridge execution services logic
- supplier marketplace core logic
- Mini App booking/payment code
- unrelated private bot flows

## Required design guardrails

### A. Reuse the truth already built
The point of A1 is to expose V1–V4 and W3 better in UI.
Do not create shadow logic in UI.

### B. No fake actionability
Do not imply:
- payment readiness if not true
- customer action completion if not evidenced
- supplier selection if not true
- message delivery if not actually sent

### C. Keep it medium-sized and coherent
This is one admin-facing visual/readability block.
Do not smuggle in unrelated backend redesign.

### D. Preserve existing architecture
No broad admin-panel rewrite.
Improve the operational surfaces you already have.

## Before coding
Output briefly:
1. current project state
2. what is already completed
3. exact block goal
4. files likely to change
5. risks
6. what remains postponed

## Suggested implementation order

1. audit current admin custom-request UI surfaces
2. identify where the richest operational/read-side truth is currently underused
3. improve list scanability first
4. improve detail sectioning and next-step visibility
5. surface prepared customer message preview clearly but safely
6. add focused tests if practical
7. keep docs/continuity updates minimal unless truly needed

## Tests required

Add focused tests only where meaningful:
1. admin UI/read adapters use existing operational hints consistently
2. prepared customer message preview does not imply delivery
3. transition/follow-through/action clarity is visible and not contradictory
4. supplier/customer semantics are not unintentionally leaked or merged

If visual/UI behavior cannot be cleanly unit-tested, keep the implementation minimal and explain.

## After coding
Report exactly:
1. files changed
2. migrations added or none
3. tests run
4. results
5. what admin-facing behavior is now improved
6. compatibility notes
7. postponed items

## Extra continuity note
This is A1: admin UI / operational surfaces for the already-built request marketplace read model.
It is not permission to redesign the broader admin system, marketplace workflow, or payment architecture.