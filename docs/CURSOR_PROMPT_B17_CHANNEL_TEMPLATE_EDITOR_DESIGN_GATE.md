# CURSOR_PROMPT_B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 5a7aa98 fix: deduplicate publishing console ui safety line
- 42a6eec feat: add publishing console admin ui metadata
- 30411b5 docs: close publishing console foundation
- 941d531 feat: add publishing console supplier offer detail view
- b38dad7 feat: add supplier offer showcase preview payload

Closed:
- B15 Publishing Console Foundation — closed
- B15P Admin UI read-only alignment — closed
- B15P.1 safety-line polish — closed
- Railway smoke passed for ui_card and safety_line deduplication

Now start:

# B17 — Channel / Template Editor Design Gate

## Critical instruction

This is DESIGN / DOCUMENTATION ONLY.

Do NOT change runtime code.
Do NOT change schemas.
Do NOT change services.
Do NOT change API routes.
Do NOT change tests.
Do NOT add migrations.
Do NOT add endpoints.
Do NOT add scheduler.
Do NOT add Telegram publish/send/retry.
Do NOT add auto-publish.
Do NOT add actual channel/template editor implementation.
Do NOT mutate any business logic.

---

## Goal

Create a design gate document for the future Channel / Template Editor layer.

This design must define how admins may eventually manage:

- channel selection
- template selection
- template variants
- language/channel formatting
- preview/edit/review workflow
- publish confirmation boundaries
- audit/idempotency requirements
- safety constraints around Telegram publishing

The output must be conservative and aligned with the already closed B15 foundation.

B17 is not implementation. It is the gate before any future editor or publish automation work.

---

## Required references

Inspect and align with:

- docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/HANDOFF_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md
- docs/HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW.md
- docs/HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md
- docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md
- docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md
- docs/BUSINESS-план-v2.txt if present in repo
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py

If some docs do not exist, report and continue with available docs.

---

## Document to create

Create:

docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md

Also update minimally:

- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if real open decisions/debt need to be recorded
- docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md only if useful as a forward reference

Do not update code or tests.

---

## Design requirements

### 1. Status and scope

State clearly:

- B17 is design-only.
- No runtime behavior is changed.
- No publish/send/scheduler/auto-publish is implemented.
- No migration.
- No frontend implementation.
- No Telegram API calls.

### 2. Product purpose

Define the future purpose of the Channel / Template Editor:

- Admin can choose or review channel strategy.
- Admin can choose or review template variant.
- Admin can preview content before any public action.
- Admin can understand whether the action is read-only, future, guarded internal preparation, or actual public publish.
- The editor must not confuse showcase readiness with booking/execution truth.

### 3. Relationship to B15 foundation

Explain that B15 already provides:

- `publish_readiness`
- `console_preview`
- `template_library`
- `preview_payload`
- `ui_card`
- supplier-offer detail read view
- guarded prepare_conversion_chain actions

B17 must build on those later, not replace them.

### 4. Channel model

Define future channel model conceptually.

Suggested channel families:

- telegram_showcase_channel
- telegram_group_discussion
- mini_app_banner
- whatsapp_broadcast
- instagram_post
- facebook_post
- external_marketplace
- none / not_configured

For each, classify:

- MVP readiness
- allowed content type
- whether direct publish is allowed in future
- whether approval is mandatory
- whether media is required
- whether CTA target is required
- audit needs

Important:
- Telegram showcase channel is the first likely executable channel.
- Other channels should remain future placeholders unless explicitly implemented later.

### 5. Template model

Define future template families and variants.

Use existing ideas from B15K / business plan:

- supplier_offer_showcase
- custom_request_cta
- tour_promotion_placeholder
- tour_promotion_rich_card
- per_seat_standard
- full_bus_private_group
- last_seats_urgent
- early_bird_discount
- supplier_service_promo
- brand_awareness_post

For each template family, define:

- source data required
- safety gates
- prohibited claims
- CTA type
- channel compatibility
- whether it can use live availability
- whether it can mention urgency/discounts

### 6. Truth and safety rules

Explicitly state:

- No fake urgency.
- No “last seats” unless live inventory confirms it.
- No discount unless source fields confirm it.
- No publish from supplier raw input.
- AI content remains draft/review only.
- Admin approval is mandatory for public publish.
- Telegram channel is softer showcase/discovery.
- Mini App / catalog / execution link is strict execution truth.
- visibility != bookability.
- publish readiness != payment/booking readiness.
- prepare_conversion_chain != Telegram publish.

### 7. Editor workflow states

Design future workflow states, without implementing them.

Suggested states:

- not_configured
- draft_available
- preview_ready
- needs_review
- blocked
- approved_for_manual_publish
- queued_for_publish
- publish_in_progress
- published
- publish_failed
- unpublished / archived

Clarify which states are future-only.

### 8. Action taxonomy

Define action types:

- safe_read
- local_preview
- edit_draft
- select_template
- select_channel
- guarded_prepare_chain
- request_approval
- confirm_publish
- schedule_publish
- retry_publish
- cancel_schedule
- unpublish / archive

Classify each as:

- allowed now
- future read-only
- future guarded mutation
- future public side effect
- forbidden until separate go/no-go

### 9. Confirmation and audit rules

Define future requirements:

- public publish must require explicit confirmation
- actor identity required
- idempotency key required for public side-effect actions
- audit rows required
- original preview snapshot must be stored before publish
- channel/message identifiers must be stored after publish
- retry must be explicit, not automatic by default
- rollback/unpublish must be separately designed

### 10. Data model sketch

Provide conceptual data model only. No migration.

Possible future entities:

- publishing_channels
- publishing_templates
- publishing_template_variants
- publishing_drafts
- publishing_attempts
- publishing_schedules
- publishing_channel_messages
- publishing_audit_events

For each, describe purpose and why it is future-only.

### 11. API sketch

Provide future API sketch only. No implementation.

Potential future endpoints:

GET:
- /admin/publishing-console/channels
- /admin/publishing-console/templates
- /admin/publishing-console/supplier-offers/{offer_id}/editor
- /admin/publishing-console/supplier-offers/{offer_id}/editor/preview

POST/PATCH:
- select template
- select channel
- update draft copy
- request approval
- confirm publish
- schedule publish
- retry publish
- cancel scheduled publish

For each endpoint, classify:
- safe_read
- draft mutation
- guarded public side effect
- future only

### 12. Frontend UX guidance

Design admin UI guidance:

- clear sections:
  - channel
  - template
  - preview
  - CTA
  - media
  - readiness
  - safety
  - audit
- use existing B15 `ui_card` and detail surfaces as input
- distinguish disabled/future actions
- show safety copy near public actions
- never show “Send now” without confirmation
- no hidden auto-publish buttons

### 13. Testing strategy for future implementation

Define future test requirements:

- read-only editor GET does not mutate
- draft edit mutates only draft state
- template/channel selection does not publish
- confirm publish requires admin auth, confirmation, actor, idempotency
- repeated publish request replays or blocks safely
- Telegram API calls mocked in tests
- publish failure creates failed attempt and does not corrupt source data
- no Layer A mutation
- no Mini App/B11 routing mutation
- no fake urgency/discount copy

### 14. Rollout plan

Recommend future incremental implementation order:

1. B17A — read-only editor detail view
2. B17B — channel/template selection metadata only
3. B17C — draft copy editor, no publish
4. B17D — manual approval state, no send
5. B17E — public publish execution design gate
6. B17F — Telegram publish implementation, only after explicit go/no-go
7. B17G — schedule/retry/unpublish design, later

### 15. Explicit non-goals

List:

- no implementation now
- no public publish now
- no scheduler now
- no auto-publish now
- no provider calls now
- no migration now
- no frontend now
- no AI public auto-send now
- no Layer A mutation
- no Mini App/B11 routing changes

---

## Update CHAT_HANDOFF

Add a concise B17 design gate entry:

- B17 Channel / Template Editor Design Gate created.
- It is design-only.
- No runtime changes.
- Recommended next remains conservative:
  - B17A read-only editor detail view, or
  - B17B selection metadata,
  - not Telegram publish implementation unless explicit go/no-go.

---

## Update OPEN_QUESTIONS_AND_TECH_DEBT

If needed, add or update a B17 item:

- channel/template editor remains future-gated
- publish automation remains future-gated
- B17 design exists as reference
- implementation not started

Keep it short.

---

## Before editing docs

Report briefly:

1. Which docs exist and were inspected.
2. Proposed B17 design doc outline.
3. Files to change.
4. Missing docs, if any.

Then edit docs.

---

## Verification

Run docs-only verification:

git diff -- docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md
git diff -- docs/CHAT_HANDOFF.md
git diff -- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
git status --short

Do not run code tests unless code changed accidentally.

---

## After editing

Report:

1. Files changed.
2. Summary of B17 design.
3. Explicit confirmation:
   - docs only
   - no runtime code
   - no schemas/services/routes/tests changed
   - no migrations
   - no Telegram/publish/scheduler/auto-publish
4. Recommended next track.

Do not commit.
Do not push.