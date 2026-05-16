# CURSOR_PROMPT_P0_OPERATIONAL_AUTOMATION_ROADMAP_CHECKPOINT

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

## Current project context

The existing `docs/IMPLEMENTATION_PLAN.md` remains the baseline MVP implementation plan and must not be replaced.

The supplier marketplace / publishing / B15-B17 work created additional operational complexity:
- many suppliers
- many supplier offers
- routes, guides, vehicles, discounts, coupons
- Telegram channel publishing
- Mini App conversion
- custom bus / RFQ requests
- customer questions
- departure operations
- passenger count notifications to suppliers
- marketing identity / QR entry tracking
- multiple AI agent roles

The project now needs a new operational automation roadmap that sits ON TOP OF:
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/TECH_SPEC_TOURS_BOT.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- existing B15/B17 publishing/editor checkpoints
- current `docs/CHAT_HANDOFF.md`
- current `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

## Goal

Create a new documentation checkpoint:

# P0 — Operational Automation Roadmap Checkpoint

This checkpoint must define the new operating model for scaling Tours_BOT from “bot + Mini App + publishing console” into an automated operations platform.

The roadmap must prevent operational chaos when many suppliers, routes, guides, discounts, customer questions, private bus requests, marketing channels, QR links, and departure operations appear at the same time.

## Critical instruction

This is DOCS ONLY.

Do NOT change runtime code.
Do NOT change app/.
Do NOT change tests/.
Do NOT change migrations.
Do NOT add endpoints.
Do NOT add Telegram publishing.
Do NOT add scheduler.
Do NOT add broadcast engine.
Do NOT add QR tokens.
Do NOT change Layer A booking/payment/reservation.
Do NOT change B11 deep link routing.
Do NOT change Publishing Console behavior.
Do NOT implement AI agents.
Do NOT implement supplier notifications.

Only documentation.

---

## Core development rule to add

The roadmap must explicitly define this execution principle:

> Work in meaningful functional blocks, not endless tiny micro-steps.
> Use narrow steps only in dangerous areas.

### Functional block mode

Use larger blocks when the area is:
- documentation / planning
- read-only models
- UI grouping
- safe summaries
- non-mutating admin visibility
- isolated helper/refactor with tests

### Narrow step mode

Split into narrow steps when the area touches:
- Layer A booking/payment/order/reservation
- payment reconciliation
- seat inventory
- migrations / schema changes
- Telegram public publish/send
- scheduler / automation workers
- marketing broadcasts
- WhatsApp/Facebook/Instagram automation
- QR ticket/order/boarding security
- supplier passenger manifests / personal data
- B11 deep link routing
- external provider calls
- permissions/auth/security
- data retention / GDPR / consent
- any irreversible public side effect

### Rule

Every future prompt must declare:
- block name
- whether it is functional-block mode or narrow-step mode
- why it is safe to be a larger block, or why it must be split
- safety boundaries
- what is explicitly not included

---

## Required new document

Create:

`docs/OPERATIONAL_AUTOMATION_ROADMAP.md`

## Required updates

Update minimally:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Optional only if natural:
- add one short forward reference in existing B17Z / B15O closure docs, if they exist and are easy to update.

Do not rewrite large old sections unnecessarily.

---

# Required content of `docs/OPERATIONAL_AUTOMATION_ROADMAP.md`

## 1. Status

State:
- P0 is a docs-only operational roadmap checkpoint.
- It does not replace `IMPLEMENTATION_PLAN.md`.
- It sits above MVP implementation plan and supplier marketplace plan.
- No runtime behavior changes are introduced by P0.

## 2. Why this roadmap exists

Explain the operational risk:

If many suppliers, guides, routes, discounts, coupons, private bus requests, customer questions, marketing posts, departure reminders, and passenger count updates arrive at once, the admin cannot manually coordinate everything.

The target model is:

Supplier gives facts  
System validates  
AI packages  
Admin controls exceptions and marketing copy  
Mini App converts  
Layer A books / accepts payment  
Workers notify / remind / escalate

## 3. Architecture invariants

Must preserve:

- Layer A booking/payment/reservation truth
- PaymentReconciliationService as payment confirmation authority
- TemporaryReservationService / Layer A seat logic
- Mini App execution truth
- B11 deep link routing
- supplier offer → tour bridge boundaries
- execution links
- Publishing Console safety gates
- service layer owns business rules
- repositories are persistence-only
- bot/UI/API do not duplicate business logic

## 4. Operational automation model

Define automation levels:

### Level 1 — Safe auto-read / auto-analysis
Examples:
- read supplier offer
- read catalog/tour status
- read readiness
- read preview
- read channel/template metadata
- group into queues
- compute warnings/blockers

### Level 2 — Auto-validation / auto-clarification
Examples:
- missing price
- missing route
- missing included/excluded
- missing discount terms
- bad photo
- missing capacity
- automatic supplier clarification draft/message, when safe

### Level 3 — Controlled internal automation
Examples:
- AI packaging draft
- dry-run conversion chain
- create/link tour if explicitly allowed in a guarded flow
- activate catalog only through existing service gates
- create execution link only through existing guarded service

### Level 4 — Public side effects, gated
Examples:
- Telegram channel publish
- schedule public post
- marketing campaign send
- supplier notification send
- passenger manifest export

Must require separate design/go-no-go, audit, confirmation, and rollback thinking.

### Level 5 — Forbidden from marketing/admin copy flows
Examples:
- manually edit price
- manually edit route
- manually edit included/excluded
- fake discount
- fake urgency
- fake “last seats”
- mutate order/payment/reservation from publishing/marketing console

## 5. Admin Automation Cockpit model

Define the cockpit queues:

- Supplier Intake Queue
- Missing Info / Clarification Queue
- Offer Readiness Queue
- Marketing Review Queue
- Publishing Queue
- Catalog / Conversion Queue
- Departure Operations Queue
- Customer Questions / Handoff Queue
- Custom Bus Requests Queue
- Risk / Conflict Queue

State that admin should work by exception, not manually process every item.

Normal flow → automated  
Risky flow → admin confirmation  
Exceptional flow → operator/admin  
Public action → gated

## 6. Supplier Intake Automation line

Define future blocks:

### A1 — Admin Automation Cockpit & Controlled Operations Design Gate
Design the cockpit, queues, action taxonomy, block-vs-narrow rules, exception handling.

### A2 — Supplier Intake Auto-Validation
Structured supplier facts, required fields, completeness/risk scoring.

### A3 — Missing Info Auto-Clarification
System asks suppliers for missing/unclear data before admin intervention.

### A4 — AI Marketing Packaging Queue
AI creates marketing drafts from locked facts.

### A5 — Admin Marketing Copy Review / Fact-Lock
Admin edits only marketing copy; supplier/catalog facts are locked.

### A6 — Controlled Catalog / Conversion Preparation
Dry-run and guarded internal conversion preparation, no public publish.

## 7. Fact-lock principle

State clearly:

Supplier owns facts:
- route
- date/time
- price
- capacity
- included
- excluded
- discounts
- coupons
- vehicle
- guide
- payment/cancellation terms

Admin may edit only marketing copy:
- headline
- hook
- short marketing description
- caption intro
- style/tone
- CTA intro
- language variant

Admin must not edit factual commercial terms from marketing console.

If factual terms need correction, system must request supplier clarification or update the source object through the proper governed flow.

## 8. Marketing cluster

Record priority cluster:

### M1 — Marketing Identity & Deep Link Capture Design Gate

Includes:
- Rezervă / Catalog CTA model
- source_channel / campaign_code / referral tracking
- audience profiles
- audience events
- initial segments
- consent baseline
- Marketing QR / Entry Points

Rules:
- Start is only technical Telegram mechanism.
- No marketing broadcast in M1.
- No Layer A mutation.
- No B11 breakage.
- No referral rewards yet.

## 9. QR cluster

Split QR clearly:

### Marketing QR / Entry Points
Belongs to M1:
- QR fence
- flyer
- bus sticker
- partner QR
- catalog QR
- exact tour QR
- referral QR

### O1 — Order / Ticket QR & Boarding Validation Design Gate
Separate future operational/security block:
- order QR
- ticket QR
- payment/order status QR
- boarding QR
- passenger check-in
- secure tokens
- boarding scans

Marketing QR must not be mixed with secure order/ticket/boarding QR.

## 10. Supplier operations cluster

Define:

### S1 — Supplier Departure Operations & Passenger Count Notifications

Purpose:
- inform suppliers how many passengers are booked/paid/confirmed for a given departure.

Future subblocks:
- S1A — read-only passenger counts per supplier/tour/departure
- S1B — supplier notification scheduling/outbox
- S1C — secure passenger manifest
- S1D — final count / departure closeout

Important:
- passenger count may be automated earlier
- passenger manifest is sensitive and must be future-gated with permissions/audit/privacy
- S1 is not marketing
- S1 must read from Layer A confirmed operational truth

## 11. AI Agent Separation Model

Define role-scoped AI agents.

### AI1 — Customer Support / Sales Assistant

Works in:
- Telegram private
- Telegram group, limited
- Mini App support

Can answer:
- tour questions
- price, if from catalog
- included/excluded, if from source
- availability, if from system
- booking/payment status, if from tools
- help/support flow

Must not:
- invent discounts
- invent availability
- confirm payment without payment truth
- change facts
- publish marketing
- approve exceptions

### AI2 — Marketing Packaging Assistant

Works for admin/content:
- post draft
- caption
- CTA variants
- language variants
- marketing summary
- warnings/missing fields

Must not:
- change facts
- publish directly
- create fake urgency
- create fake discounts
- override source of truth

### AI3 — Admin Operations Assistant

Future:
- prioritize queues
- summarize risks
- suggest next best action
- draft supplier clarification
- summarize departure operations
- recommend escalation

Must not:
- mutate critical business state
- publish/send externally without controlled action
- bypass admin confirmation

## 12. Customer self-service and handoff filter

Define that standard customer questions should be handled by AI1 / Mini App using verified data:

- price
- date
- route
- included/excluded
- seats
- booking
- payment
- boarding point
- order status

Escalate to operator/admin for:
- discount
- custom pickup
- custom bus
- complaint
- unclear payment
- large group
- custom route
- low confidence
- explicit human request

## 13. Custom bus / RFQ operations

State:
- custom bus requests must not be mixed with standard tour booking.
- They belong to the existing request marketplace / RFQ-like domain.
- Supplier responses and commercial resolution remain separate from standard order lifecycle until explicit bridge/transition.

## 14. Departure operations automation

Define:
- 7 days before departure
- 3 days before departure
- 24 hours before departure
- departure day
- post-trip

Possible automated tasks:
- check load
- remind supplier
- notify supplier of passenger count
- generate reminder content
- passenger info
- review request after trip
- next tour suggestion

Public and supplier sends require outbox/audit/governed delivery.

## 15. Block execution policy

This is critical.

Future development must follow:

### Use larger functional blocks for:
- docs-only design gates
- read-only admin views
- cockpit grouping
- safe read models
- UI summaries
- non-mutating metadata
- prompt/handoff/documentation updates

### Split into narrow steps for:
- migrations
- write models
- payment/order/reservation changes
- seat inventory
- public Telegram publish
- scheduler
- supplier notification send
- passenger manifest
- QR secure tokens
- consent/marketing broadcast
- external provider calls
- auth/permissions
- B11 routing
- AI tool execution that can mutate state

Every future prompt must include:
- Cursor mode
- block name
- prompt name
- full prompt
- handoff
- changed files expectation
- no-go list
- tests/checks
- manual verification
- commit only after report

## 16. Recommended execution order

1. P0 — Operational Automation Roadmap Checkpoint
2. A1 — Admin Automation Cockpit & Controlled Operations Design Gate
3. A2 — Supplier Intake Auto-Validation
4. A3 — Missing Info Auto-Clarification
5. A4 — AI Marketing Packaging Queue
6. A5 — Admin Marketing Copy Review / Fact-Lock
7. A6 — Controlled Catalog / Conversion Preparation
8. S1 — Supplier Departure Operations & Passenger Count Notifications
9. M1 — Marketing Identity & Deep Link Capture
10. O1 — Order / Ticket QR & Boarding Validation
11. AI1 / AI2 / AI3 detailed design gates as needed
12. Public publish/schedule/broadcast only after separate go/no-go

## 17. Non-goals of P0

P0 does not implement:
- code
- migrations
- endpoints
- Telegram publish
- supplier notifications
- marketing broadcasts
- QR tokens
- AI agents
- scheduler
- Layer A changes
- B11 changes

## 18. Success criteria

P0 is complete when:
- operational automation roadmap exists
- CHAT_HANDOFF references it
- OPEN_QUESTIONS_AND_TECH_DEBT references it
- block-vs-narrow execution policy is documented
- future priority clusters are fixed
- no runtime code changed

---

## Update `docs/CHAT_HANDOFF.md`

Add a concise current/future checkpoint:

- P0 operational automation roadmap created.
- It does not replace IMPLEMENTATION_PLAN.
- It records priority next blocks:
  - A1 Admin Automation Cockpit
  - A2/A3 supplier validation and clarification
  - A4/A5 AI packaging and fact-lock marketing review
  - S1 supplier passenger count notifications
  - M1 marketing identity / deep link capture
  - O1 secure order/ticket/boarding QR
  - AI1/AI2/AI3 separation
- It records the execution rule:
  - work in functional blocks
  - split into narrow steps on dangerous areas.

## Update `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Add a short section or bullet:

- Operational automation roadmap added.
- Open decisions:
  - supplier notification privacy scope
  - passenger manifest security
  - marketing consent and broadcast
  - QR token model
  - AI agent permissions
  - cockpit implementation order
- Keep all as future-gated.

---

## Before editing

Report briefly:
1. Which docs were inspected.
2. Proposed outline.
3. Files to change.
4. Confirmation: docs only.

Then edit.

## Verification

Run:

git diff -- docs/OPERATIONAL_AUTOMATION_ROADMAP.md
git diff -- docs/CHAT_HANDOFF.md
git diff -- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
git status --short

Do not run tests unless code changed accidentally.

## After editing

Report:
1. Files changed.
2. Summary of the roadmap.
3. Confirmation:
   - docs only
   - no app changes
   - no tests changed
   - no migrations
   - no Telegram publish
   - no scheduler
   - no broadcast
   - no QR tokens
   - no Layer A changes
4. Recommended next block: A1 design gate.

Do not commit.
Do not push.