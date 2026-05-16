# CURSOR_PROMPT_A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- d916f13 docs: add operational automation roadmap
- 2609dd1 docs: close publishing editor read-only foundation
- 3dd479f feat: add publishing editor selection metadata
- eb1473f fix: add explicit publishing editor safety flags
- e21a85f feat: add read-only publishing editor detail view

## Current planning baseline

The newly added `docs/OPERATIONAL_AUTOMATION_ROADMAP.md` is the current operational automation roadmap.

It does NOT replace:
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/TECH_SPEC_TOURS_BOT.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`

A1 is the next block after P0.

---

# A1 — Admin Automation Cockpit & Controlled Operations Design Gate

## Block mode

Functional-block mode.

Reason:
- docs-only design gate
- no runtime code
- no DB schema
- no endpoint
- no mutation
- no scheduler
- no external provider calls
- no Telegram public send
- no Layer A changes

Do not split A1 into tiny micro-steps unless you discover a safety issue in documentation alignment.

---

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
Do NOT implement admin buttons.
Do NOT implement frontend UI.

Only documentation.

---

## Goal

Create a design gate for the Admin Automation Cockpit.

The cockpit must prevent operational chaos when the platform has:

- many suppliers
- many supplier offers
- routes
- guides
- vehicles
- discounts
- coupons
- marketing content
- customer questions
- private bus / RFQ requests
- departure operations
- passenger count notifications
- QR entry points
- AI assistants

The cockpit is not a manual admin panel where admin processes everything by hand.

The target model is:

Normal flow → automated  
Risky flow → admin confirmation  
Exceptional flow → operator/admin  
Public action → gated  
Facts → supplier/catalog truth  
Marketing → AI draft + admin copy review  
Booking/payment → Layer A only

---

## Required references

Inspect and align with:

- `docs/OPERATIONAL_AUTOMATION_ROADMAP.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`
- `docs/TECH_SPEC_TOURS_BOT.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/AI_ASSISTANT_SPEC.md`
- `docs/AI_DIALOG_FLOWS.md`
- `docs/B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md`
- `docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md`
- `docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md`
- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

If some docs are missing, report and continue with available docs.

---

## Required new document

Create:

`docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md`

## Required updates

Update minimally:

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Optional only if natural:
- add a short forward reference in `docs/OPERATIONAL_AUTOMATION_ROADMAP.md` saying A1 design gate has been created.

Do not rewrite old sections unnecessarily.

---

# Required content of `docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md`

## 1. Status

State clearly:

- A1 is a docs-only design gate.
- A1 does not implement cockpit UI.
- A1 does not add buttons, routes, endpoints, DB tables, scheduler, AI agents, or supplier notifications.
- A1 defines the controlled operations model that future implementation blocks must follow.

## 2. Purpose

Explain why the cockpit is needed:

Admin cannot manually coordinate dozens of suppliers, offers, routes, guides, discounts, coupons, marketing posts, customer questions, custom bus requests, departure reminders, and passenger-count updates.

A1 designs how the system should organize work into queues, recommendations, automation levels, and exception handling.

## 3. Cockpit principles

Define:

- exception-based admin work
- system performs auto-analysis
- system groups items into queues
- system proposes next-best action
- admin edits only marketing copy
- admin does not edit supplier facts
- public actions remain gated
- Layer A remains the only booking/payment source of truth

## 4. Cockpit queues

Define each queue, purpose, data sources, sample statuses, and allowed actions.

Required queues:

### Supplier Intake Queue
Incoming supplier offers / service proposals.

### Missing Info / Clarification Queue
Offers missing required fields or containing ambiguous terms.

### Offer Readiness Queue
Offers with enough structured facts for packaging/review.

### Marketing Review Queue
AI-generated or deterministic marketing drafts waiting for admin copy review.

### Publishing Queue
Approved marketing copy / preview candidates, but public publish remains gated.

### Catalog / Conversion Queue
Items that need bridge/catalog/execution readiness checks.

### Departure Operations Queue
Upcoming departures, passenger counts, reminders, supplier operational updates.

### Customer Questions / Handoff Queue
Customer questions that AI1/Mini App cannot safely answer.

### Custom Bus Requests / RFQ Queue
Private bus / group/custom route requests separated from standard tour booking.

### Risk / Conflict Queue
Conflicting facts, suspicious discounts, unavailable routes, payment/status mismatch, privacy/security risks.

## 5. Queue card model

Define a generic cockpit card read model.

Each card should include:

- card_id
- source_type
- source_id
- title
- status
- status_tone
- priority
- next_best_action_code
- next_best_action_label
- next_best_action_kind
- next_best_action_enabled
- blocker_summary
- warning_summary
- risk_summary
- owner / responsible role
- last_updated_at
- due_at / departure_at where relevant
- safety_flags
- source_paths

No implementation, just conceptual model.

## 6. Action taxonomy

Every cockpit action must be classified as:

- safe_read
- safe_generate_draft
- supplier_clarification
- guarded_internal_action
- guarded_dry_run
- guarded_live_action
- public_side_effect
- future_disabled
- forbidden

Define rules for each.

Examples:

safe_read:
- open offer
- view supplier facts
- view preview
- view readiness
- view passenger count summary

safe_generate_draft:
- generate marketing draft from locked facts

supplier_clarification:
- ask supplier for price
- ask supplier for discount terms
- ask supplier for better photo
- ask supplier to confirm included/excluded

guarded_internal_action:
- approve package
- prepare conversion chain through existing guarded service
- activate catalog through existing service gates

guarded_dry_run:
- dry-run conversion chain
- dry-run readiness plan

public_side_effect:
- Telegram publish
- scheduled publish
- marketing campaign send
- supplier notification send
- passenger manifest export

future_disabled:
- actions visible in design but not implemented yet

forbidden:
- edit price from marketing console
- edit route from marketing console
- invent discount
- invent urgency
- mutate payment/order/reservation from cockpit

## 7. Next-best-action model

Design how the cockpit should decide recommended next action.

Examples:

- missing required fields → request_supplier_clarification
- facts complete but no package → generate_marketing_package
- package generated but not approved → review_marketing_copy
- copy approved but not conversion-ready → run_conversion_dry_run
- bridge/catalog/execution ready but not published → await_publish_go_no_go
- already published and conversion-ready → review_conversion_health
- upcoming departure → check_departure_readiness
- confirmed passengers changed → supplier_count_update_candidate
- customer asks custom bus → create_or_route_custom_request
- payment/order mismatch → escalate_operator

This is a design rule only, not implementation.

## 8. Fact-lock in cockpit

State clearly:

Supplier/catalog facts are read-only in cockpit marketing flows:

- route
- dates/times
- price
- currency
- capacity
- included
- excluded
- discount
- coupon terms
- vehicle
- guide
- cancellation/payment terms

Admin may edit only marketing copy:

- headline
- hook
- short description
- caption intro
- CTA intro
- tone/style
- language variant

If facts are wrong, action must be:
- request_supplier_clarification
- update governed source object through the proper flow
- reject/hold offer

Not:
- edit the marketing text to silently override facts

## 9. AI role integration

Design how AI agents appear in cockpit.

### AI1 — Customer Support / Sales Assistant
Used for standard customer questions using verified catalog/order/payment data.
Escalates risky cases.

### AI2 — Marketing Packaging Assistant
Generates marketing drafts from locked facts.
Cannot publish.
Cannot change facts.

### AI3 — Admin Operations Assistant
Future cockpit helper:
- summarizes queues
- explains blockers
- suggests next action
- drafts supplier clarification
- highlights departure risks

All AI actions must be tool-limited and permission-scoped.

No AI agent may mutate critical state without a controlled service action.

## 10. Supplier clarification automation

Design future behavior:

When fields are missing or ambiguous, the system should prepare/send supplier clarification requests.

Examples:

- missing price
- missing date
- missing included/excluded
- discount lacks conditions
- unclear route
- missing vehicle capacity
- low-quality photo
- unclear cancellation/payment terms

Clarification send itself is a future action requiring delivery/outbox/governance.

A1 only designs it.

## 11. Marketing review workflow

Design future flow:

Supplier facts
↓
validation
↓
AI/deterministic marketing package
↓
admin marketing copy review
↓
approve copy
↓
preview
↓
controlled publication gate

Important:
- approve copy is not publish
- approve package is not publish
- publish remains separate and gated
- marketing copy cannot override facts

## 12. Catalog / conversion workflow

Design how cockpit should surface B15/B17/B16-style readiness:

- supplier offer readiness
- publish readiness
- preview payload
- template/channel metadata
- bridge status
- catalog-visible tour
- execution link
- prepare-conversion-chain plan
- dry-run
- guarded internal prepare action

No public publish.

No Layer A mutation except through already governed booking/payment services, which A1 does not implement.

## 13. Departure operations workflow

Design future cockpit view for upcoming departures:

- departure date
- tour
- supplier
- confirmed paid passengers
- reserved unpaid
- cancelled
- available seats
- last count update
- supplier notification status
- final count readiness
- manifest status, future gated
- passenger data privacy warning

Connect to future S1:
- S1A read-only passenger counts
- S1B supplier notifications/outbox
- S1C secure passenger manifest
- S1D final count/departure closeout

A1 does not implement S1.

## 14. Customer questions / handoff workflow

Design how standard questions should be handled by AI1/Mini App, and only exceptions enter cockpit.

Standard handled automatically:
- price
- date
- route
- included/excluded
- seats
- booking status
- payment status
- boarding point

Escalate:
- discount
- custom pickup
- custom bus
- complaint
- unclear payment
- large group
- custom route
- low confidence
- explicit human request

## 15. Custom bus / RFQ workflow

Design cockpit handling for private bus/custom route requests.

Rules:
- do not mix with standard tour booking.
- RFQ/custom requests remain separate Layer C domain.
- supplier responses and commercial resolution must stay separate from standard order lifecycle until explicit bridge/transition.
- cockpit should show status and next action, not silently create orders/payments.

## 16. Safety boundaries

List explicit no-go boundaries:

- no Telegram publish in A1
- no scheduler
- no auto-publish
- no broadcast
- no supplier notification send
- no passenger manifest export
- no QR token generation
- no Layer A booking/payment/reservation mutation
- no B11 routing changes
- no AI mutation
- no external provider calls
- no migrations
- no endpoint changes

## 17. Implementation roadmap after A1

Recommend implementation order after design:

1. A1A — read-only cockpit queue contracts / DTO design
2. A1B — supplier intake queue read model
3. A1C — missing info / clarification queue read model
4. A1D — marketing review queue read model
5. A1E — catalog/conversion queue read model
6. A1F — departure operations queue read model
7. A1G — customer questions / handoff queue read model
8. A1H — custom bus / RFQ queue read model
9. A1I — cockpit summary dashboard read model
10. Later guarded actions only after separate design gates

Mark which of these can be functional-block mode and which must become narrow-step mode.

## 18. Manual UAT vision

Describe how a future admin should experience cockpit:

- open cockpit
- see queues and counts
- open priority item
- see auto-analysis
- see next-best action
- see locked facts
- edit only marketing copy when implemented
- run safe dry-run where allowed
- confirm only risky actions
- never need raw API/PowerShell for normal operations

## 19. Non-goals of A1

A1 does not implement:

- cockpit UI
- bot buttons
- endpoints
- schema
- migrations
- scheduler
- Telegram publish
- supplier notifications
- AI agents
- QR
- passenger manifest
- marketing broadcast
- Layer A changes
- B11 changes

## 20. Success criteria

A1 is complete when:

- cockpit design doc exists
- queues are defined
- action taxonomy is defined
- next-best-action model is defined
- fact-lock is defined
- AI agent boundaries are aligned
- S1/M1/O1 relationships are clear
- CHAT_HANDOFF references A1
- OPEN_QUESTIONS_AND_TECH_DEBT references A1 future-gated decisions
- no runtime files changed

---

## Update `docs/CHAT_HANDOFF.md`

Add concise A1 checkpoint:

- A1 Admin Automation Cockpit design gate created.
- Defines cockpit queues, action taxonomy, next-best-action model, fact-lock, AI role boundaries, supplier clarification, marketing review, catalog/conversion, departure ops, customer handoff, RFQ handling.
- Docs-only.
- Next recommended step: choose first read-only implementation slice, likely A1A cockpit queue contracts / DTO design or A1B supplier intake queue read model.

## Update `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Add short A1 section or bullet:

Future-gated decisions:
- cockpit persistence vs read-only projection
- supplier clarification delivery/outbox
- permissions by admin/operator/supplier roles
- AI3 permissions and tool scope
- supplier notification privacy
- passenger manifest privacy
- action audit format
- priority scoring rules
- queue SLA/due date model
- UI location: Telegram admin buttons vs web admin vs both

Keep all as future-gated.

## Optional update `docs/OPERATIONAL_AUTOMATION_ROADMAP.md`

Add one line under A1 saying:

- A1 design gate is created in `docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md`.

---

## Before editing

Report briefly:

1. Which docs were inspected.
2. Proposed outline.
3. Files to change.
4. Confirmation: docs only / functional-block mode.

Then edit.

## Verification

Run:

git diff -- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
git diff -- docs/CHAT_HANDOFF.md
git diff -- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
git diff -- docs/OPERATIONAL_AUTOMATION_ROADMAP.md
git status --short

Do not run tests unless code changed accidentally.

## After editing

Report:

1. Files changed.
2. Summary of A1 design.
3. Confirmation:
   - docs only
   - no app changes
   - no tests changed
   - no migrations
   - no endpoints
   - no Telegram publish
   - no scheduler
   - no broadcast
   - no supplier notification send
   - no QR tokens
   - no Layer A changes
   - no B11 changes
4. Recommended next block.

Do not commit.
Do not push.