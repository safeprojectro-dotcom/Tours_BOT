# CURSOR_PROMPT_A1_BLOCK1_COCKPIT_READ_ONLY_FOUNDATION

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- c95bbb8 docs: add admin automation cockpit design gate
- d916f13 docs: add operational automation roadmap
- 2609dd1 docs: close publishing editor read-only foundation
- 3dd479f feat: add publishing editor selection metadata
- eb1473f fix: add explicit publishing editor safety flags

## Current roadmap baseline

Use:

- docs/OPERATIONAL_AUTOMATION_ROADMAP.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md
- docs/B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md

## Block

A1-Block 1 — Cockpit Read-Only Foundation

## Block mode

Functional-block mode.

This block is allowed to be larger because it is read-only and non-mutating.

It may add:
- schemas
- service/read model
- admin GET route
- tests
- docs/handoff

It must NOT add:
- DB migrations
- write endpoints
- state changes
- Telegram publish
- scheduler
- supplier notifications
- QR
- Layer A booking/payment/order/reservation mutation
- B11 routing changes
- AI agent execution
- external provider calls

---

# Goal

Implement the first visible read-only Admin Automation Cockpit foundation.

The admin should be able to call one protected admin endpoint and see:

- cockpit summary
- queue counts
- priority groups
- generic cockpit cards
- supplier intake queue
- missing info / clarification queue
- offer readiness queue
- risk / conflict queue
- next-best-action metadata
- safety flags

This is the backend read-only foundation for the future button/admin UI.

---

# Required endpoint

Add protected admin endpoint:

GET /admin/automation-cockpit

Use the same admin auth pattern as existing admin routes, for example ADMIN_API_TOKEN / require_admin_api_token.

Suggested optional query params:

- limit: int = 20
- include_queues: optional comma-separated list

If query-param parsing conventions already exist in admin routes, follow project style.

---

# Required queues in this block

Implement read-only projections for these queues:

## 1. Supplier Intake Queue

Purpose:
supplier offers that exist but are not yet ready for smooth operational processing.

Possible sources:
- supplier_offers
- existing supplier offer lifecycle/status fields
- packaging/readiness metadata if available

Typical card examples:
- new supplier offer
- draft supplier offer
- offer not yet fully packaged
- offer needs moderation/review

## 2. Missing Info / Clarification Queue

Purpose:
supplier offers missing important data or with warnings/blockers.

Use existing available fields/read models where possible:
- packaging_status
- warnings
- blockers
- review package
- publish_readiness
- preview payload
- template/channel metadata

Do NOT invent business rules in route/UI.
If there is an existing service that already knows blockers/warnings, reuse it.

## 3. Offer Readiness Queue

Purpose:
offers that look ready for next internal step:
- packaging approved
- preview available
- publish readiness suggests action
- exact-tour / bridge / catalog / execution checks where already available

Do not publish.
Do not execute prepare chain.

## 4. Risk / Conflict Queue

Purpose:
cards that should catch admin attention:
- already published but still needs attention
- missing bridge/catalog/execution link
- suspicious or incomplete discount/availability facts if detectable
- no template/channel/preview where expected
- safety warnings from existing read models

Do not create new rules that can contradict existing services.
If uncertain, use conservative "needs_review" classification.

---

# Required response model

Create additive schemas in a suitable schema module, likely:

app/schemas/admin_automation_cockpit.py

or if project conventions prefer existing admin schema modules, follow them.

Response should include:

## AdminAutomationCockpitRead

Fields:
- generated_at
- summary
- queues
- safety_summary
- source_note

## summary

Include:
- total_cards
- queue_counts
- urgent_count
- needs_attention_count
- ready_count
- blocked_count
- future_disabled_count

## queue

Each queue:
- queue_code
- queue_label
- queue_status
- queue_tone
- total_count
- cards
- description
- next_refresh_hint

## card

Generic cockpit card conceptual fields:

- card_id
- source_type
- source_id
- title
- subtitle
- status
- status_label
- status_tone
- priority
- next_best_action_code
- next_best_action_label
- next_best_action_kind
- next_best_action_enabled
- blocker_summary
- warning_summary
- risk_summary
- owner_role
- last_updated_at
- due_at
- departure_at
- safety_flags
- source_paths
- metadata

## action kind enum/string values

Use these values, aligned with A1:
- safe_read
- safe_generate_draft
- supplier_clarification
- guarded_internal_action
- guarded_dry_run
- guarded_live_action
- public_side_effect
- future_disabled
- forbidden

In A1-Block 1, only safe_read and future_disabled should be enabled/visible as appropriate.
No public_side_effect action may be enabled.

## safety flags

At card and response level where helpful:
- read_only = true
- no_telegram_io = true
- no_publish_attempt = true
- no_scheduler = true
- no_auto_publish = true
- no_supplier_notification_send = true
- no_qr_token = true
- no_layer_a_mutation = true
- no_b11_change = true

---

# Service layer

Create a service such as:

app/services/admin_automation_cockpit_service.py

or project-consistent equivalent.

The route must stay thin.

The service should assemble the read model using existing services/repositories.

Strong preference:
- reuse AdminPublishingConsoleService and its existing list/detail/readiness/preview/action metadata where useful.
- do not duplicate publish readiness/business rules.
- do not duplicate supplier offer conversion rules.
- do not make internal HTTP calls if direct service access is available.

If existing services require a DB session, follow current dependency patterns.

---

# Route

Add GET route under existing admin router:

GET /admin/automation-cockpit

Rules:
- protected by admin auth
- response_model set
- no writes
- no provider calls
- no Telegram calls
- no background jobs
- no prepare_conversion_chain execution
- no publish action

---

# Classification logic

Keep it simple and conservative.

Do not over-engineer.

Use existing signals:
- console_status
- publish_readiness.status
- ui_card.status_tone
- ui_card.primary_action_enabled
- preview_payload status
- template_library metadata
- conversion_summary if available
- publication_summary if available
- safety_summary if available

Suggested mapping:

- already_published + conversion ready → risk/conflict or published review card with next action review_conversion_health
- missing blockers → missing_info
- packaging approved / preview available but not published → offer_readiness
- draft / raw / incomplete → supplier_intake
- unknown/ambiguous → risk_conflict with safe_read action

If exact source fields differ, adapt to current code and report.

---

# No-go boundaries

Absolutely do not:
- create migrations
- add DB tables
- add POST/PATCH/DELETE
- call Telegram Bot API
- publish or schedule anything
- send supplier/customer messages
- execute prepare_conversion_chain
- mutate supplier offers, tours, bridges, execution links, orders, payments, reservations, seats, content, drafts
- change Mini App routes
- change B11 deep links
- implement AI agents
- introduce external calls

---

# Tests

Add focused unit/API tests.

Likely file:

tests/unit/test_admin_automation_cockpit.py

or project convention equivalent.

Required tests:

1. GET /admin/automation-cockpit returns 401/403 without admin token.
2. GET /admin/automation-cockpit returns 200 with admin token.
3. Response contains summary, queues, safety_summary.
4. Required queue codes exist:
   - supplier_intake
   - missing_info
   - offer_readiness
   - risk_conflict
5. Cards use allowed action kinds only.
6. No public_side_effect action is enabled.
7. safety_summary confirms no Telegram IO, no scheduler, no supplier notification send, no QR, no Layer A mutation, no B11 change.
8. Existing admin publishing console tests still pass.

Run:

python -m compileall app tests

python -m pytest tests/unit/test_admin_automation_cockpit.py -q
python -m pytest tests/unit/test_admin_publishing_console.py -q
python -m pytest tests/unit/test_supplier_offer_publish_readiness.py -q
python -m pytest tests/unit/test_supplier_offer_review_package.py -q
python -m pytest tests/unit/test_admin_publishing_console_prepare_chain_action.py -q
python -m pytest tests/unit/test_prepare_conversion_chain_d2d_affordance.py -q

If a test file does not exist or names differ, report and run the relevant closest tests.

---

# Docs

Create:

docs/HANDOFF_A1_BLOCK1_COCKPIT_READ_ONLY_FOUNDATION.md

Update minimally:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md

Document:
- endpoint
- queues implemented
- read-only boundaries
- safety flags
- tests
- next recommended block

Do not rewrite large sections.

---

# Before coding

Before editing files, report briefly:

1. Existing admin route/auth pattern found.
2. Existing publishing console services/schemas that will be reused.
3. Proposed new files.
4. Proposed route.
5. Proposed tests.
6. Explicit no-go list.

Then implement.

---

# After coding

Report:

1. Files changed.
2. Endpoint added.
3. Queues implemented.
4. Response model summary.
5. How admin auth is preserved.
6. How read-only/no-side-effect boundaries are enforced.
7. Tests run and results.
8. Any deviations from planned scope.
9. Confirm:
   - no migrations
   - no app writes / no POST/PATCH/DELETE
   - no Telegram publish/send
   - no scheduler
   - no supplier notification send
   - no QR tokens
   - no Layer A mutation
   - no B11 changes
   - no AI agent execution
   - no external provider calls

Do not commit.
Do not push.