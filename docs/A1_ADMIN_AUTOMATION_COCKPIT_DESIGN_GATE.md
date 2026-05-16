# A1 - Admin Automation Cockpit & Controlled Operations Design Gate

## 1. Status

**A1 is a docs-only design gate.**

A1 does **not** implement:

- cockpit UI
- admin buttons
- routes or endpoints
- DB tables or migrations
- scheduler
- AI agents
- supplier notifications
- Telegram publish/send
- QR tokens
- Layer A booking/payment/reservation changes
- B11 deep-link routing changes

A1 defines the controlled operations model that future implementation blocks must follow.

## 2. Purpose

The admin cannot manually coordinate dozens of suppliers, offers, routes, guides, discounts, coupons, marketing posts, customer questions, custom bus requests, departure reminders, and passenger-count updates.

The cockpit is the future exception-oriented operations surface. It should organize work into queues, show automated analysis, recommend next best actions, and separate safe reads from guarded or public actions.

Target model:

- normal flow -> automated
- risky flow -> admin confirmation
- exceptional flow -> operator/admin
- public action -> gated
- facts -> supplier/catalog truth
- marketing -> AI draft + admin copy review
- booking/payment -> Layer A only

## 3. Cockpit Principles

- Admin works by exception, not by manually processing every item.
- System performs auto-analysis and groups items into queues.
- System proposes next-best actions with clear disabled reasons and blockers.
- Admin edits only marketing copy in marketing flows.
- Admin does **not** edit supplier facts from the cockpit.
- Public actions remain gated with separate design/go-no-go.
- Layer A remains the only booking/payment/reservation source of truth.
- Mini App remains customer execution truth.
- Publishing Console and B17 editor safety gates remain inputs, not bypasses.
- Bot/UI/API stay thin; business rules live in services.

## 4. Cockpit Queues

Each queue below is a design target. A1 does not implement read models or UI.

### Supplier Intake Queue

**Purpose:** incoming supplier offers / service proposals.

**Likely data sources:** supplier offers, supplier profile, intake metadata, packaging/moderation status.

**Sample statuses:** `new`, `needs_validation`, `ready_for_review`, `blocked`, `archived`.

**Allowed actions:** safe read, request clarification draft, validate facts, route to readiness queue.

### Missing Info / Clarification Queue

**Purpose:** offers missing required fields or containing ambiguous commercial/operational terms.

**Likely data sources:** supplier offer fields, packaging draft, content-quality review, media quality checks.

**Sample statuses:** `missing_price`, `missing_route`, `missing_capacity`, `unclear_discount`, `needs_supplier_reply`.

**Allowed actions:** safe read, draft supplier clarification, hold/reject, mark clarification pending. Actual sends require future outbox/delivery design.

### Offer Readiness Queue

**Purpose:** offers with enough structured facts for packaging/review.

**Likely data sources:** moderation package, packaging status, fact completeness, media readiness.

**Sample statuses:** `ready_for_packaging`, `package_generated`, `needs_content_review`, `blocked_by_fact_gap`.

**Allowed actions:** safe read, generate draft where already supported by governed flows, open review package, escalate blockers.

### Marketing Review Queue

**Purpose:** AI-generated or deterministic marketing drafts waiting for admin copy review.

**Likely data sources:** packaging draft, fact-lock review, preview payloads, template library, publishing editor metadata.

**Sample statuses:** `draft_ready`, `copy_needs_review`, `fact_warning`, `approved_copy`, `blocked`.

**Allowed actions:** safe read, edit marketing copy in a future B17C-like slice, approve copy in a future guarded flow. Facts stay locked.

### Publishing Queue

**Purpose:** approved marketing copy / preview candidates. Public publish remains gated.

**Likely data sources:** publish readiness, console preview, template/channel metadata, editor safety flags.

**Sample statuses:** `preview_ready`, `needs_channel_config`, `blocked_by_gate`, `await_publish_go_no_go`, `published_elsewhere`.

**Allowed actions:** safe read, preview, dry-run readiness. `confirm_publish` / `schedule_publish` stay future-disabled until separate go/no-go.

### Catalog / Conversion Queue

**Purpose:** items that need bridge/catalog/execution readiness checks.

**Likely data sources:** supplier-offer review package, bridge state, catalog visibility, execution links, prepare-conversion-chain plan/action affordance.

**Sample statuses:** `needs_bridge`, `catalog_not_active`, `missing_execution_link`, `dry_run_ready`, `already_prepared`.

**Allowed actions:** safe read, dry-run plan, guarded internal prepare action through existing approved services when implemented in the relevant slice. No public publish.

### Departure Operations Queue

**Purpose:** upcoming departures, passenger counts, reminders, supplier operational updates.

**Likely data sources:** tours, bookings, reservations, orders/payments, departure time, supplier linkage.

**Sample statuses:** `upcoming`, `count_changed`, `needs_supplier_update`, `manifest_future_gated`, `departure_today`.

**Allowed actions:** read passenger counts, draft update, escalate operations risk. Supplier sends/manifests are future-gated.

### Customer Questions / Handoff Queue

**Purpose:** customer questions that AI1/Mini App cannot safely answer.

**Likely data sources:** handoffs, conversations, Mini App/order context, Telegram user context.

**Sample statuses:** `needs_operator`, `low_confidence`, `custom_request`, `payment_unclear`, `resolved`.

**Allowed actions:** safe read, assign operator, summarize context, route to appropriate queue. AI must not confirm facts beyond verified sources.

### Custom Bus Requests / RFQ Queue

**Purpose:** private bus / group/custom route requests separated from standard tour booking.

**Likely data sources:** custom requests, supplier responses, RFQ status, operator workflow.

**Sample statuses:** `new_request`, `await_supplier`, `needs_operator`, `proposal_ready`, `closed`.

**Allowed actions:** safe read, route to RFQ flow, draft supplier/operator clarification. Must not silently create standard orders/payments.

### Risk / Conflict Queue

**Purpose:** conflicting facts, suspicious discounts, unavailable routes, payment/status mismatch, privacy/security risks.

**Likely data sources:** content-quality warnings, payment/order visibility, publish readiness, operational checks, audit events.

**Sample statuses:** `fact_conflict`, `payment_mismatch`, `privacy_risk`, `unsafe_claim`, `needs_admin_decision`.

**Allowed actions:** safe read, escalate, block publish/automation, request correction through governed source flows.

## 5. Queue Card Model

Generic cockpit cards should be read-model projections. Conceptual fields:

- `card_id`
- `source_type`
- `source_id`
- `title`
- `status`
- `status_tone`
- `priority`
- `next_best_action_code`
- `next_best_action_label`
- `next_best_action_kind`
- `next_best_action_enabled`
- `blocker_summary`
- `warning_summary`
- `risk_summary`
- `owner` / responsible role
- `last_updated_at`
- `due_at` / `departure_at` where relevant
- `safety_flags`
- `source_paths`

This is conceptual only; no schema is added in A1.

## 6. Action Taxonomy

Every cockpit action must be classified:

| Kind | Rule |
|------|------|
| `safe_read` | Read-only navigation or detail view. No mutation or external send. |
| `safe_generate_draft` | Generates internal draft/preview from locked facts; no public send. |
| `supplier_clarification` | Requests or drafts missing-info questions; actual send requires delivery/outbox governance. |
| `guarded_internal_action` | Mutates internal business state through existing service gates and audit/idempotency where needed. |
| `guarded_dry_run` | Simulates an internal action; no mutation. |
| `guarded_live_action` | Confirmed internal mutation with clear actor, audit, and rollback/failure behavior. |
| `public_side_effect` | Sends/publishes/exports externally; requires separate design/go-no-go, confirmation, audit, idempotency. |
| `future_disabled` | Visible as future metadata only; not executable. |
| `forbidden` | Must not be offered from cockpit/marketing/admin copy flows. |

Examples:

**`safe_read`**

- open offer
- view supplier facts
- view preview
- view readiness
- view passenger count summary

**`safe_generate_draft`**

- generate marketing draft from locked facts

**`supplier_clarification`**

- ask supplier for price
- ask supplier for discount terms
- ask supplier for better photo
- ask supplier to confirm included/excluded

**`guarded_internal_action`**

- approve package
- prepare conversion chain through existing guarded service
- activate catalog through existing service gates

**`guarded_dry_run`**

- dry-run conversion chain
- dry-run readiness plan

**`public_side_effect`**

- Telegram publish
- scheduled publish
- marketing campaign send
- supplier notification send
- passenger manifest export

**`future_disabled`**

- actions visible in design but not implemented yet

**`forbidden`**

- edit price from marketing console
- edit route from marketing console
- invent discount
- invent urgency
- mutate payment/order/reservation from cockpit

## 7. Next-best-action Model

The cockpit should recommend the next safe action based on verified state.

Design examples:

| Condition | Recommended next action |
|-----------|-------------------------|
| Missing required fields | `request_supplier_clarification` |
| Facts complete but no package | `generate_marketing_package` |
| Package generated but not approved | `review_marketing_copy` |
| Copy approved but not conversion-ready | `run_conversion_dry_run` |
| Bridge/catalog/execution ready but not published | `await_publish_go_no_go` |
| Already published and conversion-ready | `review_conversion_health` |
| Upcoming departure | `check_departure_readiness` |
| Confirmed passengers changed | `supplier_count_update_candidate` |
| Customer asks custom bus | `create_or_route_custom_request` |
| Payment/order mismatch | `escalate_operator` |

This is a design rule only, not implementation.

## 8. Fact-lock in Cockpit

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

If facts are wrong, the action must be one of:

- `request_supplier_clarification`
- update governed source object through the proper flow
- reject/hold offer

Not:

- edit the marketing text to silently override facts

## 9. AI Role Integration

AI appears in the cockpit as role-scoped assistance, not unrestricted autonomy.

### AI1 - Customer Support / Sales Assistant

Used for standard customer questions using verified catalog/order/payment data. Escalates risky cases.

Must not invent discounts, availability, payment status, or factual claims.

### AI2 - Marketing Packaging Assistant

Generates marketing drafts from locked facts.

Cannot publish. Cannot change facts. Cannot create fake urgency or discounts.

### AI3 - Admin Operations Assistant

Future cockpit helper:

- summarizes queues
- explains blockers
- suggests next action
- drafts supplier clarification
- highlights departure risks

All AI actions must be tool-limited and permission-scoped. No AI agent may mutate critical state without a controlled service action.

## 10. Supplier Clarification Automation

Future behavior:

When fields are missing or ambiguous, the system should prepare supplier clarification requests.

Examples:

- missing price
- missing date
- missing included/excluded
- discount lacks conditions
- unclear route
- missing vehicle capacity
- low-quality photo
- unclear cancellation/payment terms

Clarification **send** itself is a future action requiring delivery/outbox/governance. A1 only designs it.

## 11. Marketing Review Workflow

Future flow:

1. Supplier facts
2. Validation
3. AI/deterministic marketing package
4. Admin marketing copy review
5. Approve copy
6. Preview
7. Controlled publication gate

Important:

- approve copy is not publish
- approve package is not publish
- publish remains separate and gated
- marketing copy cannot override facts

## 12. Catalog / Conversion Workflow

The cockpit should surface B15/B17/B16-style readiness:

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

## 13. Departure Operations Workflow

Future cockpit view for upcoming departures:

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

## 14. Customer Questions / Handoff Workflow

Standard questions should be handled by AI1/Mini App when verified data is available:

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

## 15. Custom Bus / RFQ Workflow

Cockpit handling for private bus/custom route requests:

- do not mix with standard tour booking
- RFQ/custom requests remain separate Layer C domain
- supplier responses and commercial resolution stay separate from standard order lifecycle until explicit bridge/transition
- cockpit shows status and next action, not silent order/payment creation

## 16. Safety Boundaries

No-go boundaries for A1:

- no Telegram publish
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

## 17. Implementation Roadmap After A1

Use larger functional blocks for read-only, design, and non-mutating work. Split into narrow steps only when implementation touches migrations, Layer A, payment/order/reservation, seat inventory, public sends, scheduler, supplier notifications, passenger manifests, QR security, consent, permissions, B11, external providers, or mutating AI tools.

Recommended next implementation grouping:

| Block | Scope | Mode |
|-------|-------|------|
| **A1-Block 1 - Cockpit Read-Only Foundation** | Queue contracts, generic cockpit card model, summary dashboard, supplier intake queue, missing info queue, offer readiness queue, risk/conflict queue. | Larger functional block if read-only and non-mutating. |
| **A1-Block 2 - Commercial / Marketing / Conversion Queues** | Marketing review queue, publishing queue, catalog/conversion queue, fact-lock presentation, next-best-action rules, B15/B17 integration. | Larger functional block if read-only and non-mutating. |
| **A1-Block 3 - Operations / Handoff / RFQ Queues** | Departure operations queue, customer questions/handoff queue, custom bus/RFQ queue, supplier passenger count read-only summaries, privacy warnings. | Larger functional block for read-only counts/summaries; split if notifications/manifests appear. |
| **A1-Block 4 - Guarded Actions Design Gate** | Supplier clarification send, dry-run actions, internal prepare actions, supplier notification send, public publish, audit/permissions/confirmation model. | Design gate can be a functional block; implementation must split into narrow steps for sends, mutations, audit, permissions, and public effects. |

Optional reference sub-slices such as queue contracts, supplier intake queue, missing-info queue, marketing review queue, catalog/conversion queue, departure operations queue, handoff queue, RFQ queue, and cockpit summary can still be used for internal planning, but **A1A-A1I are not the required next execution order**.

## 18. Manual UAT Vision

Future admin experience:

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

## 20. Success Criteria

A1 is complete when:

- cockpit design doc exists
- queues are defined
- action taxonomy is defined
- next-best-action model is defined
- fact-lock is defined
- AI agent boundaries are aligned
- S1/M1/O1 relationships are clear
- `docs/CHAT_HANDOFF.md` references A1
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` references A1 future-gated decisions
- no runtime files changed

## Related

- `docs/OPERATIONAL_AUTOMATION_ROADMAP.md`
- `docs/AI_ASSISTANT_SPEC.md`
- `docs/AI_DIALOG_FLOWS.md`
- `docs/B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md`
- `docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md`
