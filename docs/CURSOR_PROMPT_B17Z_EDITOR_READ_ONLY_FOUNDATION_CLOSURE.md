# CURSOR_PROMPT_B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 3dd479f feat: add publishing editor selection metadata
- eb1473f fix: add explicit publishing editor safety flags
- e21a85f feat: add read-only publishing editor detail view
- cf28cd3 docs: add channel template editor design gate
- 5a7aa98 fix: deduplicate publishing console ui safety line

Closed and smoke-verified:
- B17 — Channel / Template Editor Design Gate
- B17A — Read-only Channel / Template Editor Detail View
- B17A.1 — Explicit editor safety/action flags
- B17B — Channel / Template Selection Metadata Only
- Railway smoke passed for:
  - GET /admin/publishing-console/supplier-offers/12/editor
  - safety flags
  - disabled confirm_publish / schedule_publish
  - channel_selection / template_selection response metadata
  - no selection persistence

Now implement:

# B17Z — Editor Read-only Foundation Closure Checkpoint

## Critical instruction

This is DOCUMENTATION / CLOSURE ONLY.

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
Do NOT add POST/PATCH.
Do NOT add persistence.
Do NOT mutate any business logic.

---

## Goal

Create a closure checkpoint for the B17 read-only editor foundation.

The document must summarize:

1. What B17 design gate defined.
2. What B17A implemented.
3. What B17A.1 corrected.
4. What B17B implemented.
5. Which read-only editor surfaces are now available.
6. Which selection metadata is response-only and not persisted.
7. Which future editor/publish capabilities remain gated.
8. What was smoke-verified on Railway.
9. Recommended next tracks:
   - Marketing cluster M1
   - QR cluster / O1
   - or B17C design-only if product chooses editor continuation

---

## Required references

Inspect and align with:

- docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md
- docs/HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md
- docs/HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md
- docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/CHAT_HANDOFF.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/HANDOFF_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py

If some docs do not exist, report and continue with available docs.

---

## Document to create

Create:

docs/B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md

Also update minimally:

- docs/CHAT_HANDOFF.md
- docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if current text is misleading

Do not update code or tests.

---

## Required content of B17Z closure doc

### 1. Status

State clearly:

- B17 read-only editor foundation is closed.
- B17Z is documentation / architecture closure only.
- No runtime changes in B17Z.
- No migration.
- No Telegram/public side effects.

### 2. Scope closed

Summarize closed slices:

- B17 — design gate
- B17A — GET-only editor detail endpoint:
  - GET /admin/publishing-console/supplier-offers/{offer_id}/editor
- B17A.1 — explicit machine-readable safety/action flags
- B17B — channel_selection / template_selection response metadata only

### 3. Available read-only editor surface

Document:

GET /admin/publishing-console/supplier-offers/{offer_id}/editor

It returns:

- channel_section
- template_section
- preview_section
- cta_section
- media_section
- readiness_section
- safety_section
- future_actions
- source_snapshot
- channel_selection
- template_selection

### 4. Source snapshot

Document that editor detail reuses existing B15/B15P data:

- publish_readiness
- console_preview
- template_library
- preview_payload
- ui_card
- safety_summary

### 5. Safety flags

Document explicit safety flags:

- read_only=true
- no_telegram_io=true
- no_publish_attempt=true
- no_scheduler=true
- no_auto_publish=true
- no_prepare_chain_execution=true
- no_layer_a_mutation=true
- no_mini_app_b11_change=true

### 6. Selection metadata

Document B17B:

- channel_selection is response metadata only
- template_selection is response metadata only
- no DB persistence
- no POST/PATCH
- no channel selection save
- no template selection save
- no draft edit save
- no editor state save

### 7. Disabled future public actions

Document:

- confirm_publish exists only as disabled future metadata
- schedule_publish exists only as disabled future metadata
- both enabled=false
- actual public publish remains future-gated

### 8. Railway smoke evidence

Summarize operator smoke:

For offer 12:

- endpoint returned 200
- ChannelRecommended=telegram_showcase_channel
- ChannelCurrentStatus=configured
- ChannelOptionsCount=2
- TelegramConfigured=True
- TelegramRecommended=True
- TelegramCurrent=True
- TemplateSelected=custom_request_cta
- TemplateRecommended=custom_request_cta
- TemplateOptionsCount=2
- CustomRequestAvailable=available
- CustomRequestRecommended=True
- CustomRequestCurrent=True
- ConfirmPublishEnabled=False
- SchedulePublishEnabled=False
- SafetyReadOnly=True
- NoTelegramIo=True
- NoPublishAttempt=True
- NoAutoPublish=True

### 9. What is intentionally not done

List explicitly:

- no channel/template persistence
- no draft copy editor
- no approval state persistence
- no Telegram publish/send
- no scheduler
- no auto-publish
- no batch publish
- no publish attempts
- no prepare_conversion_chain execution from GET
- no Layer A mutation
- no Mini App/B11 routing changes
- no migration

### 10. Future gated work

Future only, separate design/go-no-go:

- B17C — draft-copy editor design gate
- persistent channel/template selection
- approval workflow
- public publish execution
- schedule/retry/unpublish
- Telegram publish implementation
- campaign/channel automation

### 11. Relationship to upcoming priority clusters

Record that after current structure closure, two high-priority clusters are next:

#### Marketing cluster

M1 — Marketing Identity & Deep Link Capture Design Gate

Includes:
- Rezervă / Catalog CTA model
- source/campaign/referral tracking
- audience profiles
- audience events
- segments
- consent baseline
- Marketing QR / Entry Points

No marketing broadcasts in M1.

#### QR cluster

Split QR into:

1. Marketing QR / Entry Points
   - QR fence / flyer / bus / partner / catalog / exact tour / referral
   - belongs to M1

2. Secure Order / Ticket / Boarding QR
   - booking QR
   - payment/order status QR
   - boarding QR
   - passenger check-in
   - secure tokens
   - boarding scans
   - future block O1 — Order / Ticket QR & Boarding Validation Design Gate

### 12. Recommended next

Recommend:

1. Close B17Z now.
2. Then open M1 design gate.
3. Keep O1 as next QR/security design block after M1 or when operational QR becomes priority.
4. Do not jump to publish automation.

---

## Update CHAT_HANDOFF

Add concise B17Z closure entry:

- B17 read-only editor foundation closed.
- B17/B17A/B17A.1/B17B done.
- GET /admin/publishing-console/supplier-offers/{offer_id}/editor is the read-only editor surface.
- channel_selection / template_selection are response metadata only, not persisted.
- No Telegram/public automation.
- Next priority clusters: M1 Marketing Identity / Deep Link Capture and O1 QR / Boarding Validation design gate.

---

## Update B17 design gate

Add a small closure note:

- B17Z closed the read-only editor foundation.
- Further B17C+ mutations remain future-gated.

---

## Update OPEN_QUESTIONS_AND_TECH_DEBT

Only if needed:

- Mark B17 read-only editor foundation as closed.
- Keep persistent selection/draft/publish automation as future-gated.
- Mention M1/O1 priority if useful.

---

## Before editing docs

Report briefly:

1. Which docs exist and were inspected.
2. Proposed new closure doc outline.
3. Files to change.
4. Any missing docs.

Then edit docs.

---

## Verification

Run docs-only verification:

git diff -- docs/B17Z_EDITOR_READ_ONLY_FOUNDATION_CLOSURE.md
git diff -- docs/CHAT_HANDOFF.md
git diff -- docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md
git diff -- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
git status --short

Do not run code tests unless code changed accidentally.

---

## After editing

Report:

1. Files changed.
2. Summary of closure.
3. Explicit confirmation:
   - docs only
   - no runtime code
   - no tests changed
   - no migrations
   - no Telegram/publish/scheduler/auto-publish
4. Recommended next track.

Do not commit.
Do not push.