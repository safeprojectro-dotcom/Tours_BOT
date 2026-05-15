# CURSOR_PROMPT_B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 941d531 feat: add publishing console supplier offer detail view
- b38dad7 feat: add supplier offer showcase preview payload
- 283e5bc feat: add publishing console template library metadata
- 6bfe7d8 feat: add publishing console preview display metadata
- f63244 docs: record publish readiness suggest-only smoke

Closed and smoke-verified manually:
- B15G — guarded auto-publish design only
- B15H — read-only publish readiness metadata + smoke
- B15I — suggest-only publish readiness display metadata + smoke
- B15F2/B15F3 — publishing console preview display metadata + smoke
- B15K — publishing console template_library metadata + smoke
- B15L — supplier-offer showcase preview_payload metadata + smoke
- B15M — supplier-offer publishing console detail read view + smoke

Latest B15M Railway smoke:
GET /admin/publishing-console/supplier-offers/12 returned:
- supplier_offer_id=12
- candidate_key=supplier_offer:12
- kind=supplier_offer_initial
- publish_readiness.status=already_published
- console_preview.preview_status=available
- template_library.family=supplier_offer_showcase
- preview_payload.payload_status=available
- tour_code=B10-SO12-04fb1f
- has_tour_bridge=true
- has_catalog_visible_tour=true
- has_active_execution_link=true
- publication_summary.already_published=true
- safety_summary.read_only=true
- no_telegram_io=true
- no_publish_attempt=true
- no_prepare_chain_execution=true
- no_layer_a_mutation=true

Now implement:

# B15O — Publishing Console Foundation Closure Checkpoint

## Critical instruction

This is DOCUMENTATION / CLOSURE ONLY.

Do NOT change runtime code.
Do NOT change schemas.
Do NOT change services.
Do NOT change API routes.
Do NOT change tests.
Do NOT add migration.
Do NOT add endpoints.
Do NOT add scheduler.
Do NOT add Telegram publish/send/retry.
Do NOT add auto-publish.
Do NOT mutate any business logic.

---

## Goal

Create a closure checkpoint for the B15 Publishing Console Foundation track.

The document must summarize:

1. What B15 publishing console foundation now provides.
2. Which read-only surfaces are available.
3. Which guarded mutation endpoints exist and what they do.
4. Which public side effects are still NOT implemented.
5. Which safety boundaries were preserved.
6. What was smoke-verified on Railway.
7. What future work is allowed only behind separate design/go-no-go gates.
8. Recommended next track after B15O.

---

## Required references

Inspect and align with:

- docs/CHAT_HANDOFF.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW.md
- docs/HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md
- docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md
- docs/HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md
- docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md
- docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md
- docs/B15H_READ_ONLY_PUBLISH_READINESS_SMOKE.md
- docs/B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX_SMOKE.md
- docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md
- docs/B16D2_PREPARE_CONVERSION_CHAIN_EXECUTION_DESIGN_GATE.md
- docs/B16D2E_PREPARE_CONVERSION_CHAIN_PRODUCTION_SMOKE.md
- docs/B15E2_PUBLISHING_CONSOLE_PREPARE_CHAIN_SMOKE.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md
- docs/TECH_SPEC_TOURS_BOT_v1.1.md

If some docs do not exist, report and continue with available docs.

---

## Document to create

Create:

docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md

Also update minimally:

- docs/CHAT_HANDOFF.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md only if a real open decision/debt should be changed

Do not update code or tests.

---

## Required content of B15O closure doc

### 1. Status

State clearly:

- B15 Publishing Console Foundation: closed.
- Closure type: documentation/architecture checkpoint.
- No runtime changes in B15O.
- No migration.
- No Telegram/public side effects.

### 2. Scope closed

Summarize closed B15/B16 supporting slices:

- B16D2C — guarded admin prepare_conversion_chain endpoint.
- B16D2D — action affordance metadata.
- B16D2E — production smoke for prepare_conversion_chain.
- B15E2 — publishing console prepare_conversion_chain action execution.
- B15E2 smoke.
- B15G — guarded auto-publish design only.
- B15H — publish_readiness metadata.
- B15H smoke.
- B15I — suggest-only display metadata.
- B15I smoke.
- B15F2/B15F3 — console_preview display metadata.
- B15F2/B15F3 smoke.
- B15K — template_library metadata.
- B15K smoke.
- B15L — preview_payload metadata.
- B15L smoke.
- B15M — supplier-offer detail read view.
- B15M smoke.

### 3. Available admin read surfaces

Document available GET/read surfaces:

- `GET /admin/publishing-console`
- `GET /admin/publishing-console?kind=supplier_offer_initial`
- `GET /admin/publishing-console/supplier-offers/{offer_id}`
- `GET /admin/supplier-offers/{offer_id}/review-package`
- `GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan`

Explain what each gives.

### 4. Available guarded mutation surfaces

Document mutation surfaces that exist, but clarify they are guarded and not public publish automation:

- `POST /admin/supplier-offers/{offer_id}/prepare-conversion-chain`
- `POST /admin/publishing-console/supplier-offers/{offer_id}/prepare-conversion-chain`

Explain:
- internal chain only
- bridge/catalog/execution link preparation
- idempotency required
- confirm required for live
- dry_run supported
- no Telegram I/O
- no Layer A mutation
- no orders/payments/reservations/seats mutation

### 5. Read-model objects now available

Document key read-model objects:

- `publish_readiness`
  - status
  - can_suggest_manual_publish
  - can_auto_publish=false
  - auto_publish_mode=disabled
  - gates
  - summary/badge/next action/primary blocker/warnings/gate summary

- `console_preview`
  - compact preview status/template family/summary/safety

- `template_library`
  - family
  - selected/recommended template
  - available templates
  - future/not implemented variants

- `preview_payload`
  - title/body/caption/CTA/media/channel/warnings/blockers/safety

- supplier-offer detail view:
  - publish_readiness
  - console_preview
  - template_library
  - preview_payload
  - conversion summary
  - linked tour summary
  - publication summary
  - safety summary

### 6. Safety boundaries preserved

Explicitly state:

- No auto-publish.
- No scheduler.
- No Telegram send/publish/retry.
- No hidden publish.
- No publish attempts created from read endpoints.
- No prepare_conversion_chain execution from GET/read surfaces.
- No Layer A booking/payment/order/reservation/seat mutation.
- No Mini App/B11 routing changes.
- No migration in this read-model line.
- `can_auto_publish` remains false.
- Public publish remains explicit, guarded, and separate from internal conversion preparation.
- Telegram channel remains softer showcase/discovery surface.
- Mini App / execution/catalog layer remains strict execution truth.
- visibility != bookability.

### 7. Railway smoke evidence

Summarize production smoke results:

- B16D2E prepare_conversion_chain smoke on offer 12:
  - dry_run passed
  - live passed
  - replay passed
  - already_prepared
  - no Telegram / no Layer A

- B15E2 publishing-console prepare-chain smoke:
  - dry_run passed
  - live passed
  - replay passed
  - actor_surface=publishing_console
  - no Telegram / no Layer A

- B15H smoke:
  - `publish_readiness` visible in review-package and console
  - can_auto_publish=false
  - auto_publish_mode=disabled

- B15I smoke:
  - summary/badge/next action/gate summary visible
  - can_auto_publish=false

- B15F2/F3 smoke:
  - console_preview visible
  - tour_promotion placeholder/read-only

- B15K smoke:
  - template_library visible
  - tour_promotion variants future/not implemented

- B15L smoke:
  - preview_payload visible
  - tour_promotion source=tour_placeholder
  - safety note says no Telegram API calls

- B15M smoke:
  - detail endpoint returned supplier_offer:12 detail
  - publish_readiness / console_preview / template_library / preview_payload all visible
  - safety_summary flags true

### 8. What is intentionally not done

List explicitly:

- No public auto-publish.
- No scheduled publish.
- No Telegram automatic send.
- No batch publish.
- No channel editor.
- No template editor that persists selections.
- No real tour promotion post generator.
- No Mini App routing changes.
- No payment/order/reservation/seat changes.
- No supplier execution retries.
- No AI-generated public text auto-send.

### 9. Future work gates

Define future work that requires separate design/go-no-go:

- Channel/template editor.
- Scheduled publish after explicit approval.
- Batch approval.
- Actual Telegram publish automation.
- Auto-publish.
- Tour promotion post generation.
- Durable media storage/rendering.
- Provider retry policy.
- Public post edit/delete/unpublish workflow.
- Admin frontend UI buttons that execute publish.

### 10. Recommended next track

Recommend one of these next:

Option A — B15P Admin UI polish/read-only frontend alignment:
- copy/labels
- button affordances
- display groups
- no new backend mutation

Option B — B17 Channel/template editor design gate:
- design only first
- no implementation of send/publish

Option C — B18 Public publish automation go/no-go design:
- only if user explicitly wants to move toward Telegram publish automation

Recommendation should be conservative:
- Close B15 foundation now.
- Next safe block: admin UI polish/read-only alignment or channel/template editor design gate.
- Do not jump directly to auto-publish.

---

## Update CHAT_HANDOFF

Add a concise B15O closure entry:

- B15 Publishing Console Foundation closed.
- Current clean checkpoint should be recorded after commit by user, but use placeholder “pending commit” if needed.
- Mention available read surfaces and guarded prepare-chain actions.
- Mention no Telegram/public automation.

---

## Update B15 closure checkpoint

Update existing closure checkpoint to mark B15O as final closure:

- foundation closed
- B15B–B15M/B15O summary
- future options separated from closed foundation
- no runtime changes in B15O

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

- git diff -- docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md
- git diff -- docs/CHAT_HANDOFF.md
- git diff -- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- git status --short

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