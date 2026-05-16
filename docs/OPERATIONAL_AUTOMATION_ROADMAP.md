# P0 - Operational Automation Roadmap Checkpoint

## 1. Status

**P0 is a docs-only operational roadmap checkpoint.**

This document does **not** replace `docs/IMPLEMENTATION_PLAN.md`. It sits above the MVP implementation plan, the supplier marketplace plan (`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`), the technical specs, and the B15/B17 publishing/editor checkpoints.

P0 introduces **no runtime behavior changes**:

- no code
- no migrations
- no endpoints
- no Telegram publishing
- no scheduler
- no broadcast engine
- no QR tokens
- no Layer A booking/payment/reservation changes
- no B11 deep-link routing changes
- no Publishing Console behavior changes
- no AI agent implementation
- no supplier notification implementation

## 2. Why This Roadmap Exists

Tours_BOT has moved beyond a simple "bot + Mini App" shape. The supplier marketplace and publishing-console work add many parallel operational streams:

- many suppliers and supplier offers
- routes, guides, vehicles, discounts, coupons
- Telegram channel publishing
- Mini App conversion
- custom bus / RFQ requests
- customer questions and handoffs
- departure operations
- passenger count notifications to suppliers
- marketing identity / QR entry tracking
- multiple AI assistant roles

If all of this is handled manually, operators will eventually coordinate too much at once. The target model is:

1. Supplier gives facts.
2. System validates.
3. AI packages drafts.
4. Admin controls exceptions and marketing copy.
5. Mini App converts.
6. Layer A books and accepts payment.
7. Workers notify, remind, and escalate only through governed flows.

## 3. Architecture Invariants

Future automation must preserve:

- Layer A booking/payment/reservation truth
- `PaymentReconciliationService` as payment confirmation authority
- `TemporaryReservationService` / Layer A seat logic
- Mini App execution truth
- B11 deep-link routing
- supplier offer -> tour bridge boundaries
- execution links
- Publishing Console safety gates
- service layer ownership of business rules
- repositories as persistence-only infrastructure
- bot/UI/API as thin delivery surfaces that do not duplicate business logic

Publishing, marketing, AI, QR, and supplier-ops flows must never bypass these invariants.

## 4. Operational Automation Model

### Level 1 - Safe Auto-read / Auto-analysis

Safe, non-mutating reads and summaries:

- read supplier offer
- read catalog/tour status
- read readiness
- read preview
- read channel/template metadata
- group into queues
- compute warnings/blockers

These are usually safe as larger functional blocks when they remain read-only and test-covered.

### Level 2 - Auto-validation / Auto-clarification

Structured checks and safe clarification drafting:

- missing price
- missing route
- missing included/excluded
- missing discount terms
- bad photo
- missing capacity
- automatic supplier clarification draft/message, when safe

Supplier sends still need a delivery policy, outbox/audit, and privacy review before automation.

### Level 3 - Controlled Internal Automation

Internal operations that may mutate system state but do not create public side effects:

- AI packaging draft
- dry-run conversion chain
- create/link tour only when explicitly allowed in a guarded flow
- activate catalog only through existing service gates
- create execution link only through existing guarded service

These must use explicit service methods, audit/idempotency where appropriate, and narrow tests.

### Level 4 - Public Side Effects, Gated

Public or external sends:

- Telegram channel publish
- schedule public post
- marketing campaign send
- supplier notification send
- passenger manifest export

These require separate design/go-no-go, audit, confirmation, idempotency, privacy review, and rollback/failure thinking.

### Level 5 - Forbidden From Marketing/Admin Copy Flows

Marketing/admin copy surfaces must not mutate source facts or operational truth:

- manually edit price
- manually edit route
- manually edit included/excluded
- fake discount
- fake urgency
- fake "last seats"
- mutate order/payment/reservation from publishing/marketing console

Fact corrections must go through source-object or supplier-clarification flows, not marketing copy tools.

## 5. Admin Automation Cockpit Model

The future cockpit should let admins work by exception, not manually process every item.

Core queues:

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

Operating principle:

- normal flow -> automated
- risky flow -> admin confirmation
- exceptional flow -> operator/admin
- public action -> gated

## 6. Supplier Intake Automation Line

### A1 - Admin Automation Cockpit & Controlled Operations Design Gate

Design the cockpit, queues, action taxonomy, functional-block vs narrow-step rules, exception handling, and safety boundaries.

Design gate created: `docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md`.

**A1-Block 1 (read-only foundation):** `GET /admin/automation-cockpit` — see `docs/HANDOFF_A1_BLOCK1_COCKPIT_READ_ONLY_FOUNDATION.md`.

### A2 - Supplier Intake Auto-validation

Structured supplier facts, required fields, completeness scoring, and risk scoring.

### A3 - Missing Info Auto-clarification

System asks suppliers for missing or unclear data before admin intervention, using governed messaging/outbox rules when sends are introduced.

### A4 - AI Marketing Packaging Queue

AI creates marketing drafts from locked source facts.

### A5 - Admin Marketing Copy Review / Fact-lock

Admin edits only marketing copy. Supplier/catalog facts remain locked.

### A6 - Controlled Catalog / Conversion Preparation

Dry-run and guarded internal conversion preparation. No public publish.

## 7. Fact-lock Principle

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

Admin must not edit factual commercial terms from the marketing console. If factual terms need correction, the system must request supplier clarification or update the source object through the proper governed flow.

## 8. Marketing Cluster

### M1 - Marketing Identity & Deep Link Capture Design Gate

M1 records how marketing entry points map into verified Mini App and bot flows.

Includes:

- Rezerva / Catalog CTA model
- `source_channel` / `campaign_code` / referral tracking
- audience profiles
- audience events
- initial segments
- consent baseline
- Marketing QR / Entry Points

Rules:

- `/start` is only the technical Telegram mechanism.
- No marketing broadcast in M1.
- No Layer A mutation.
- No B11 breakage.
- No referral rewards yet.

## 9. QR Cluster

Marketing QR and secure operational QR must stay separate.

### Marketing QR / Entry Points

Belongs to M1:

- QR fence
- flyer
- bus sticker
- partner QR
- catalog QR
- exact tour QR
- referral QR

These identify marketing entry/campaign context. They are not tickets, proof of payment, or boarding credentials.

### O1 - Order / Ticket QR & Boarding Validation Design Gate

Separate future operational/security block:

- order QR
- ticket QR
- payment/order status QR
- boarding QR
- passenger check-in
- secure tokens
- boarding scans

O1 must define token model, expiry, permissions, scan audit, privacy, offline/duplicate scan behavior, and fallback operations before implementation.

## 10. Supplier Operations Cluster

### S1 - Supplier Departure Operations & Passenger Count Notifications

Purpose:

- inform suppliers how many passengers are booked/paid/confirmed for a given departure

Future subblocks:

- S1A - read-only passenger counts per supplier/tour/departure
- S1B - supplier notification scheduling/outbox
- S1C - secure passenger manifest
- S1D - final count / departure closeout

Important:

- passenger count may be automated earlier
- passenger manifest is sensitive and must be future-gated with permissions/audit/privacy
- S1 is not marketing
- S1 must read from Layer A confirmed operational truth

## 11. AI Agent Separation Model

Role-scoped AI agents reduce accidental authority leakage.

### AI1 - Customer Support / Sales Assistant

Works in:

- Telegram private
- Telegram group, limited
- Mini App support

Can answer from verified data:

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

### AI2 - Marketing Packaging Assistant

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

### AI3 - Admin Operations Assistant

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

## 12. Customer Self-service and Handoff Filter

Standard customer questions should be handled by AI1 / Mini App using verified data:

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

## 13. Custom Bus / RFQ Operations

Custom bus requests must not be mixed with standard tour booking.

They belong to the existing request marketplace / RFQ-like domain. Supplier responses and commercial resolution remain separate from standard order lifecycle until an explicit bridge/transition is designed.

## 14. Departure Operations Automation

Milestones:

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

## 15. Block Execution Policy

Future work should be planned in meaningful functional blocks, not endless tiny micro-steps. Use narrow steps only in dangerous areas.

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

Every future prompt should declare:

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

## 16. Recommended Execution Order

1. P0 - Operational Automation Roadmap Checkpoint
2. A1 - Admin Automation Cockpit & Controlled Operations Design Gate
3. A2 - Supplier Intake Auto-validation
4. A3 - Missing Info Auto-clarification
5. A4 - AI Marketing Packaging Queue
6. A5 - Admin Marketing Copy Review / Fact-lock
7. A6 - Controlled Catalog / Conversion Preparation
8. S1 - Supplier Departure Operations & Passenger Count Notifications
9. M1 - Marketing Identity & Deep Link Capture
10. O1 - Order / Ticket QR & Boarding Validation
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

## 18. Success Criteria

P0 is complete when:

- operational automation roadmap exists
- `docs/CHAT_HANDOFF.md` references it
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` references it
- block-vs-narrow execution policy is documented
- future priority clusters are fixed
- no runtime code changed

## Related

- `docs/IMPLEMENTATION_PLAN.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/TECH_SPEC_TOURS_BOT.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md`
