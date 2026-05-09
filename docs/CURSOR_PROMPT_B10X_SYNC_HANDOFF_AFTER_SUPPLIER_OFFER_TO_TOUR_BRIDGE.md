# CURSOR_PROMPT_B10X_SYNC_HANDOFF_AFTER_SUPPLIER_OFFER_TO_TOUR_BRIDGE

You are continuing the Tours_BOT project.

## Before coding / before editing

This is a documentation-sync step, not a feature implementation step.

Current business architecture:

- Telegram Channel = marketing showcase.
- Telegram Bot = router / consultant / entry point, not duplicate Mini App catalog.
- Mini App = execution truth and conversion.
- Layer A = booking/payment authority.
- Supplier Offer = raw supplier proposal / source facts.
- Tour = customer-facing sellable catalog object.
- Admin = final decision maker.
- AI = draft generator only, not final publisher.

Core principle:

- visibility != bookability
- Mini App execution truth must stay strict and current.
- Telegram/channel can be softer showcase, but must not contradict Mini App truth.

## Source documents to read first

Read these before making changes:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md
- docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md
- docs/IMPLEMENTATION_PLAN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/MINI_APP_UX.md
- docs/AI_DIALOG_FLOWS.md
- docs/AI_ASSISTANT_SPEC.md
- docs/TESTING_STRATEGY.md
- docs/COMMIT_PUSH_DEPLOY.md

If some files are missing, do not invent content. Update only what exists and mention missing files in the final report.

## Current completed business checkpoints to record

B0–B4.3 completed:
- Supplier Offer intake, structured data, AI/deterministic packaging, human-readable formatting, marketing template rules, pricing/discount/availability truth rules.

B5 completed:
- Admin packaging review.
- approved_for_publish means package approved, not Telegram publish and not Mini App activation.

B6 completed:
- Branded Telegram preview JSON.

B7.1 completed:
- Media review metadata.

B7.2 completed:
- Card render preview plan.
- No real pixels/download/storage yet.

B9 completed:
- Explicit Supplier Offer → Tour Bridge Design.
- Bridge must be explicit admin action.
- No silent ORM trigger.
- No AI-created Tour.
- No supplier bypass.

B10 completed:
- Admin bridge implementation.
- Approved Supplier Offer creates/links Tour.
- Bridge is idempotent.
- Tour is created as draft.
- No Telegram publish.
- No booking/payment side effects during bridge.

B10.1 completed:
- Smoke passed.
- Supplier Offer #8 → Tour #4.
- Draft Tour not visible in Mini App catalog until activation.

B10.2 completed:
- Admin activate-for-catalog gate.
- Tour draft → open_for_sale via explicit admin endpoint.
- Bridge creation and catalog activation are separate.

B10.3 completed:
- Full bus catalog conversion semantics.
- Fixed full_bus supplier offer is bookable as whole-bus package.
- full_bus fixed offer ≠ custom request.
- per_seat = customer books individual seats.
- full_bus = customer books whole bus/package.
- custom_request = separate flow for another route/date/bus/capacity.
- UI/policy must not say “choose 5 seats” for full_bus.

B10.4 completed:
- Fixed full_bus reservation execution.
- seats_count forced to full vehicle capacity.
- total_amount for FULL_BUS = base_price package total, not base_price * seats_count.
- Per-seat unchanged.

B10.5 completed:
- Boarding fallback fixed for full_bus fixed charter without real boarding points.
- No fake boarding_point_id=1.
- Preparation summary works.
- Reservation/payment/My bookings path works.
- Production smoke passed:
  Supplier Offer #8 → Tour #4 → open_for_sale → Reserve bus → preparation → reservation → payment-entry/mock complete → My bookings.

## Important postponed item to record

B10.6 is postponed.

Reason:
Telegram bot currently duplicates too much Mini App content and may show old/full-bus-inconsistent text.

Future B10.6 should make Telegram Bot a router/consultant, not duplicate catalog:

- short summary
- open exact Tour in Mini App
- ask question/help
- request custom trip

This is not critical now because Mini App execution path works.

## This step goal

Update project continuity documents so that the next agent can safely continue with:

1. B8 — Recurring Supplier Offers on top of the explicit bridge.
2. Then B7.3 — publish-safe media pipeline, only after storage/download policy is decided.
3. Then continue back to the business plan.

## Expected files to change

Prefer only documentation files:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md or the actual business-plan file used in repo
- optional: docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md if it already tracks this B-series continuation
- optional: docs/COMMIT_PUSH_DEPLOY.md only if it has a specific handoff/checklist section that must be updated

Do not edit code in this step.

## Required updates

### docs/CHAT_HANDOFF.md

Add a current checkpoint section:

- Current checkpoint: B10.5 completed / B10.6 postponed / next safe step B8.
- Record the production smoke:
  Supplier Offer #8 → Tour #4 → open_for_sale → Reserve bus → preparation → reservation → payment-entry/mock complete → My bookings.
- Record the architectural rule:
  Bridge creation != catalog activation != Telegram publish != booking/payment.
- Record that Tour created from Supplier Offer starts as draft and becomes bookable only after explicit admin activation.
- Record full_bus fixed package semantics:
  - seats_count forced to vehicle capacity
  - total_amount = package total
  - no per-seat UI wording
  - boarding fallback must not fake boarding_point_id
- Record B10.6 as postponed and non-blocking.

### docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Add or update sections for:

1. B10.6 Telegram Bot router/consultant redesign postponed
   - risk: bot duplicates Mini App truth or shows stale/inconsistent full_bus copy
   - accepted now because Mini App execution path is strict and passed smoke
   - revisit trigger: before Telegram deep-link routing / B11 or before major group/private bot promotion

2. Publish-safe media pipeline unresolved
   - B7.3 postponed until storage/download/media policy is decided
   - no real pixels/download/storage yet

3. Recurring Supplier Offers upcoming risk
   - B8 must generate/link Tour instances through explicit service/admin logic
   - no silent cron/ORM creation without admin-governed policy
   - no hidden publish/bookability side effects
   - recurrence generation must preserve bridge and activation separation

### Business plan document

Mark B10–B10.5 as completed if not already recorded.

Clarify next order:

- First: B10.x documentation sync
- Next: B8 Recurring Supplier Offers on top of bridge
- Then: B7.3 publish-safe media pipeline when storage/download policy is decided
- Then: B11 Telegram Deep Link Routing or the next approved business-plan step

Clarify B8 dependency:

- recurring supplier offers must use explicit Supplier Offer template → Tour instances logic
- generated Tour instances should start as draft or controlled inactive state unless the step explicitly implements safe activation policy
- no automatic Telegram publish
- no booking/payment side effects during recurrence generation

## Safety boundaries / non-goals

Do not:
- implement B8 in this step
- change app code
- change migrations
- change payment/order/reservation logic
- change Telegram bot behavior
- implement B10.6
- implement media storage/download/card rendering
- create Telegram publish side effects
- create supplier lifecycle side effects
- silently activate tours
- create recurring tours automatically outside explicit admin/service rules

## Required final report

After editing, report:

1. Files changed
2. Exact sections updated
3. Confirmation that no code/migrations were changed
4. Next recommended prompt name for B8
5. Tests/checks run
6. Any missing docs or ambiguity found