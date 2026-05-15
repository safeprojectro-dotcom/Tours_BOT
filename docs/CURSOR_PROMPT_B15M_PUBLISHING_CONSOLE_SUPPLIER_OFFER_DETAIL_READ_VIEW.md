# CURSOR_PROMPT_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- b38dad7 feat: add supplier offer showcase preview payload
- 283e5bc feat: add publishing console template library metadata
- 6bfe7d8 feat: add publishing console preview display metadata
- f63244 docs: record publish readiness suggest-only smoke
- 06cc17 feat: add publish readiness suggest-only display metadata

Closed:
- B15G — guarded auto-publish design only
- B15H — read-only publish readiness metadata
- B15I — suggest-only publish readiness display metadata
- B15F2/B15F3 — publishing console preview display metadata
- B15K — publishing console template_library metadata
- B15L — supplier-offer showcase preview_payload metadata
- B15K/B15L short Railway read-only smoke passed manually:
  GET /admin/publishing-console returned console_preview, template_library, preview_payload for read-only rows.
  Tour-promotion rows remain placeholder/not_applicable and safety notes confirm no Telegram publish/schedule/channel send.

Now implement:

# B15M — Admin Publishing Console Supplier-offer Detail Read View

## Goal

Add a read-only admin detail view for a specific supplier-offer publishing console candidate.

The current publishing console list exposes many useful row-level objects:
- publish_readiness
- console_preview
- template_library
- preview_payload
- actions
- review_package_path
- prepare_conversion_chain_plan_path
- related metadata

B15M should expose a single detail read view for one supplier offer, so admin/OPS can inspect all publishing-console-related readiness/preview/template data in one structured response.

This is a read-only detail endpoint/read model.

---

## Critical boundary

Do NOT publish.
Do NOT send Telegram messages.
Do NOT retry Telegram messages.
Do NOT schedule publish.
Do NOT implement auto-publish.
Do NOT create publish attempts.
Do NOT execute prepare_conversion_chain.
Do NOT mutate supplier offers, tours, bridges, execution links, orders, payments, reservations, or seats.
Do NOT create migration.
Do NOT change Mini App routing.
Do NOT change B11 deep-link behavior.
Do NOT introduce provider/Telegram API calls.

No public side effects.

---

## Required references

Inspect and align with:

- docs/CHAT_HANDOFF.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md
- docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md
- docs/HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md
- docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md
- docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py
- app/schemas/admin_publish_readiness.py
- app/services/supplier_offer_publish_readiness.py
- app/services/admin_navigation_paths.py
- app/api/routes/admin.py

If some docs do not exist, report and continue with available docs.

---

## Current foundation to preserve

Publishing console list rows already include:

- `candidate_key`
- `kind`
- `title`
- `subtitle`
- `console_status`
- `next_best_action`
- `human_summary`
- `publish_readiness`
- `console_preview`
- `template_library`
- `preview_payload`
- `actions`
- `review_package_path`
- `prepare_conversion_chain_plan_path`
- `prepare_conversion_chain_action`
- `offer_debug`
- `template_kind`
- `channel_kind`
- `channel_status`

Do not remove or break existing list fields.

Prefer additive changes.

---

## Desired endpoint

Add a read-only admin endpoint for supplier-offer publishing console detail.

Preferred route shape:

GET /admin/publishing-console/supplier-offers/{offer_id}

Alternative if existing style suggests another route:

GET /admin/publishing-console/supplier-offer/{offer_id}

Choose the style that best fits the project, but keep it narrow and supplier-offer-specific.

Admin auth must be preserved by existing `/admin` router dependencies.

---

## Desired response

Create a detail response schema, for example:

`AdminPublishingConsoleSupplierOfferDetailRead`

Suggested fields:

```text
supplier_offer_id: int
candidate_key: str
kind: "supplier_offer_initial"
title: str | null
subtitle: str | null
console_status: str
human_summary: str | null
operator_summary: str | null

review_package_path: str
prepare_conversion_chain_plan_path: str | null
publish_action_path: str | null

publish_readiness: AdminPublishReadinessRead
console_preview: AdminPublishingConsolePreviewRead
template_library: AdminPublishingConsoleTemplateLibraryRead
preview_payload: AdminPublishingConsolePreviewPayloadRead

actions: list[AdminPublishingConsoleActionRead]
prepare_conversion_chain_action: AdminPrepareConversionChainActionAffordanceRead | null

conversion_summary:
  has_tour_bridge: bool | null
  has_catalog_visible_tour: bool | null
  has_active_execution_link: bool | null
  next_missing_step: str | null

linked_tour_summary:
  tour_id: int | null
  tour_code: str | null
  tour_status: str | null
  catalog_listed_for_mini_app: bool | null

publication_summary:
  lifecycle_status: str | null
  published_at: datetime | null
  showcase_chat_id: str | null
  showcase_message_id: int | null
  already_published: bool

safety_summary:
  read_only: true
  no_telegram_io: true
  no_publish_attempt: true
  no_prepare_chain_execution: true
  no_layer_a_mutation: true
  note: str

generated_at: datetime