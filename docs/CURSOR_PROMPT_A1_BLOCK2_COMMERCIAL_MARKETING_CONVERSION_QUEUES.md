# CURSOR_PROMPT_A1_BLOCK2_COMMERCIAL_MARKETING_CONVERSION_QUEUES

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoint:

- 8f9180e feat: add read-only admin automation cockpit
- c95bbb8 docs: add admin automation cockpit design gate
- d916f13 docs: add operational automation roadmap
- 2609dd1 docs: close publishing editor read-only foundation
- 3dd479f feat: add publishing editor selection metadata

## Previous block

A1-Block 1 — Cockpit Read-Only Foundation is complete.

Implemented:

- GET /admin/automation-cockpit
- AdminAutomationCockpitRead
- supplier_intake queue
- missing_info queue
- offer_readiness queue
- risk_conflict queue
- generic cockpit cards
- summary counts
- safety_summary
- tests

Railway smoke PASS:

- TotalCards = 20
- supplier_intake = 0
- missing_info = 6
- offer_readiness = 5
- risk_conflict = 9
- safety flags true:
  - read_only
  - no_telegram_io
  - no_publish_attempt
  - no_scheduler
  - no_supplier_notification_send
  - no_qr_token
  - no_layer_a_mutation
  - no_b11_change

## Current block

# A1-Block 2 — Commercial / Marketing / Conversion Queues

## Block mode

Functional-block mode.

This block is allowed to be larger because it is still read-only and non-mutating.

It may add:

- additive response fields
- schemas
- service/read-model logic
- tests
- docs/handoff

It must NOT add:

- DB migrations
- write endpoints
- POST/PATCH/DELETE
- Telegram publish/send
- scheduler
- supplier notification send
- QR tokens
- Layer A booking/payment/order/reservation mutation
- B11 routing changes
- AI execution
- external provider calls

---

# Goal

Extend the existing read-only Admin Automation Cockpit so it exposes the commercial / marketing / conversion flow more clearly.

The admin should see separate queues for:

1. Marketing Review
2. Publishing Queue
3. Catalog / Conversion Queue

These should complement the existing queues:

- supplier_intake
- missing_info
- offer_readiness
- risk_conflict

The purpose is to show the business flow:

Supplier Offer / Tour
↓
Marketing Review
↓
Publishing Readiness
↓
Catalog / Conversion Readiness
↓
Next Best Action

This is still read-only.

---

# Required endpoint behavior

Extend existing endpoint only:

GET /admin/automation-cockpit

Do not add a new endpoint unless project conventions strongly require it.

The endpoint should now include these additional queue codes:

- marketing_review
- publishing_queue
- catalog_conversion

The existing `include_queues` filter must work with the new queues.

Invalid queue names should continue to behave as currently implemented.

---

# Required new queues

## 1. marketing_review

Purpose:

Items where admin should review or understand marketing package / preview / copy readiness.

Use existing fields/read models where possible:

- console_preview
- template_library
- preview_payload
- ui_card
- publish_readiness
- packaging/readiness metadata if available

Card should answer:

- Is a preview available?
- Is a template selected?
- Is payload available?
- Is this marketing copy/package ready or needs attention?
- Is this a future editor action?

Expected next actions:

- open_marketing_review
- open_preview
- review_template
- review_missing_marketing_data
- future_edit_marketing_copy

Allowed action kinds:

- safe_read
- future_disabled

No marketing edit persistence in this block.

No AI generation in this block.

---

## 2. publishing_queue

Purpose:

Items where public publication status/readiness matters.

Use existing B15/B17 read models where possible:

- publish_readiness.status
- publication_summary.already_published where available
- ui_card.status
- ui_card.primary_action
- console_status
- safety_summary

Card should answer:

- Is the item already published?
- Is it ready for publish suggestion?
- Is publish blocked?
- Is publish intentionally future-gated?
- What should admin do next?

Expected next actions:

- review_publish_readiness
- review_already_published
- resolve_publish_blocker
- await_publish_go_no_go
- future_confirm_publish

Allowed action kinds:

- safe_read
- future_disabled

No publish.
No Telegram send.
No publish attempt.
No scheduler.

---

## 3. catalog_conversion

Purpose:

Items where Mini App catalog / Tour / bridge / execution readiness matters.

Use existing fields/read models where possible:

- conversion_summary
- linked_tour_summary
- prepare_conversion_chain_action
- prepare_conversion_chain_plan_path
- publish_readiness
- B15/B16 read surfaces already exposed in publishing-console detail/editor if available

Card should answer:

- Is there a linked tour?
- Is the tour visible in catalog?
- Is there an active execution link?
- Is prepare-conversion-chain needed?
- Is only dry-run / review plan appropriate?
- Is conversion already prepared?

Expected next actions:

- review_conversion_health
- open_prepare_chain_plan
- run_conversion_dry_run_future
- review_catalog_visibility
- resolve_conversion_blocker

Allowed action kinds:

- safe_read
- future_disabled

No live prepare_conversion_chain execution.
No dry-run execution in this block unless already implemented in A1-Block 1, which it is not.
No Layer A mutation.

---

# Card metadata improvements

Extend cockpit cards in an additive way if useful.

Add a `commercial_context` or `context_summary` object/string if appropriate.

It may include safe read-only metadata such as:

- supplier_offer_id
- tour_id
- tour_code
- already_published
- has_tour_bridge
- has_catalog_visible_tour
- has_active_execution_link
- preview_status
- payload_status
- template_family
- selected_template_id
- publish_status
- prepare_chain_status
- fact_lock_note

Do not include sensitive passenger/customer data.

Do not expose secrets or tokens.

If adding a nested schema is too heavy, use metadata safely.

---

# Fact-lock presentation

Cards in marketing/commercial queues should clearly communicate:

- supplier/catalog facts are read-only
- admin may review marketing copy
- admin must not edit price/route/included/excluded/discount from cockpit
- factual corrections must go through supplier clarification or governed source update

This can be a string field in metadata or safety_flags/context_summary.

Do not implement editing.

---

# Next-best-action rules

Keep conservative and deterministic.

Suggested mapping:

## Marketing Review

- preview_payload available + template selected → open_marketing_review
- preview missing / payload unavailable → review_missing_marketing_data
- template future/blocked → review_template
- marketing edit not implemented → future_edit_marketing_copy, future_disabled

## Publishing Queue

- already_published → review_already_published or review_conversion_health
- publish_readiness.status ready / can_suggest_manual_publish → review_publish_readiness
- blocked / needs_attention → resolve_publish_blocker
- actual publish action → future_confirm_publish, future_disabled

## Catalog / Conversion

- has_tour_bridge + catalog visible + execution link → review_conversion_health
- missing execution link / catalog not visible → open_prepare_chain_plan
- prepare chain action available but not executed → run_conversion_dry_run_future or open_prepare_chain_plan
- unknown → review_conversion_health or resolve_conversion_blocker

No hidden mutation.

---

# Safety summary

Existing response-level safety_summary must remain.

If adding queue/card-level safety, preserve:

- read_only = true
- no_telegram_io = true
- no_publish_attempt = true
- no_scheduler = true
- no_auto_publish = true
- no_supplier_notification_send = true
- no_qr_token = true
- no_layer_a_mutation = true
- no_b11_change = true

No public_side_effect action may be enabled.

No guarded_live_action may be enabled.

---

# Service layer

Reuse existing:

- AdminAutomationCockpitService
- AdminPublishingConsoleService
- publishing-console read models
- detail/editor read helper logic if already accessible safely

Do not duplicate business rules from publishing readiness/conversion readiness.

Route must remain thin.

No internal HTTP calls if direct service access exists.

---

# Tests

Update or add focused tests in:

tests/unit/test_admin_automation_cockpit.py

Required coverage:

1. GET /admin/automation-cockpit still returns 200 with admin token.
2. Required existing queues still exist:
   - supplier_intake
   - missing_info
   - offer_readiness
   - risk_conflict
3. New queues exist:
   - marketing_review
   - publishing_queue
   - catalog_conversion
4. include_queues works with new queues.
5. New cards expose safe action kinds only.
6. No public_side_effect action is enabled.
7. No guarded_live_action is enabled.
8. marketing/commercial cards include fact-lock or read-only context.
9. safety_summary remains true for all no-go boundaries.
10. Existing admin publishing console tests still pass.

Run:

python -m compileall app tests

python -m pytest tests/unit/test_admin_automation_cockpit.py -q
python -m pytest tests/unit/test_admin_publishing_console.py -q
python -m pytest tests/unit/test_supplier_offer_publish_readiness.py -q
python -m pytest tests/unit/test_supplier_offer_review_package.py -q
python -m pytest tests/unit/test_admin_publishing_console_prepare_chain_action.py -q
python -m pytest tests/unit/test_prepare_conversion_chain_d2d_affordance.py -q

---

# Docs

Create:

docs/HANDOFF_A1_BLOCK2_COMMERCIAL_MARKETING_CONVERSION_QUEUES.md

Update minimally:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/A1_ADMIN_AUTOMATION_COCKPIT_DESIGN_GATE.md
- docs/OPERATIONAL_AUTOMATION_ROADMAP.md if useful

Document:

- new queues
- read-only boundaries
- fact-lock presentation
- tests
- recommended next block

Do not rewrite large sections.

---

# Before coding

Before editing files, report briefly:

1. Existing A1-Block 1 service/schema/route structure found.
2. Which publishing-console fields will be reused.
3. Proposed schema/service additions.
4. Proposed tests.
5. Explicit no-go list.

Then implement.

---

# After coding

Report:

1. Files changed.
2. Queues added.
3. Response model additions.
4. How fact-lock is represented.
5. How next-best-actions are assigned.
6. How read-only/no-side-effect boundaries are preserved.
7. Tests run and results.
8. Any deviations from planned scope.
9. Confirm:
   - no migrations
   - no write endpoints
   - no POST/PATCH/DELETE
   - no Telegram publish/send
   - no scheduler
   - no supplier notification send
   - no QR tokens
   - no Layer A mutation
   - no B11 changes
   - no AI execution
   - no external provider calls

Do not commit.
Do not push.