# CURSOR_PROMPT_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 6bfe7d8 feat: add publishing console preview display metadata
- f63244 docs: record publish readiness suggest-only smoke
- 06cc17 feat: add publish readiness suggest-only display metadata
- 48c65cf docs: record publish readiness read-only smoke
- 30321e9 feat: add read-only publish readiness metadata

Closed:
- B15G — guarded auto-publish design only
- B15H — read-only publish readiness metadata
- B15I — suggest-only publish readiness display metadata
- B15F2/B15F3 — publishing console preview display metadata
- B15F2/B15F3 short Railway smoke passed manually:
  GET /admin/publishing-console returned console_preview for tour_promotion rows:
  preview_status=placeholder, template_family=tour_promotion, safety_note confirms read-only/no Telegram publish/schedule/channel send.

Now implement:

# B15K — Publishing Console Template Library / Preview Layer Block

## Goal

Build a stronger read-only template/preview layer for the admin publishing console.

This block should make publishing console rows easier to understand by showing:

1. Which template family applies.
2. Which template variants are possible.
3. Which variant is selected/recommended.
4. Whether preview is available, placeholder-only, blocked, or not applicable.
5. What preview content exists from current safe read data.
6. What is missing before a real publish could ever be considered.
7. Why no public action is executed.

This is a read-only console/product clarity block.

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

No public side effects.

---

## Required references

Inspect and align with:

- docs/CHAT_HANDOFF.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md
- docs/HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md
- docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md
- docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md
- docs/B15H_READ_ONLY_PUBLISH_READINESS_SMOKE.md
- docs/B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX_SMOKE.md
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py
- app/schemas/admin_publish_readiness.py
- app/services/supplier_offer_publish_readiness.py
- app/services/admin_navigation_paths.py

If some docs do not exist, report and continue with available docs.

---

## Current foundation to preserve

Publishing console rows already include:

- candidate_key
- kind
- title/subtitle
- next_best_action
- human_summary
- publish_readiness
- console_preview
- template_kind/template_version/template_preview_available
- channel_kind/channel_status
- actions

B15F2/F3 added/readied `console_preview`.

Do not remove or break existing fields.

Prefer additive changes.

---

## Desired output

Add or refine a read-only template library / preview layer.

Suggested new/additive objects:

### 1. template_library

A compact object describing possible templates for a row.

Example shape:

```text
template_library:
  family: "supplier_offer_showcase" | "tour_promotion" | "unknown"
  selected_template_id: str | null
  recommended_template_id: str | null
  template_version: str | null
  available_templates:
    - template_id: str
      label: str
      description: str
      status: "available" | "future" | "not_applicable" | "blocked"
      disabled_reason: str | null
  selection_reason: str | null
  safety_note: str