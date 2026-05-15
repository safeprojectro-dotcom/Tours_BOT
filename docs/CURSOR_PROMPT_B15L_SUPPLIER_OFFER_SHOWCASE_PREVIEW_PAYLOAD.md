# CURSOR_PROMPT_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 283e5bc feat: add publishing console template library metadata
- 6bfe7d8 feat: add publishing console preview display metadata
- f63244 docs: record publish readiness suggest-only smoke
- 06cc17 feat: add publish readiness suggest-only display metadata
- 48c65cf docs: record publish readiness read-only smoke

Closed:
- B15G — guarded auto-publish design only
- B15H — read-only publish readiness metadata
- B15I — suggest-only publish readiness display metadata
- B15F2/B15F3 — publishing console preview display metadata
- B15K — publishing console template library metadata
- B15K short Railway smoke passed manually:
  GET /admin/publishing-console returned template_library for tour_promotion rows:
  template_family=tour_promotion, selected_template_id=tour_promotion_placeholder,
  available_templates=future, safety_note confirms read-only/no Telegram publish/schedule/channel send.

Now implement:

# B15L — Supplier-offer Showcase Preview Payload Expansion

## Goal

Improve `supplier_offer_initial` rows in the admin publishing console with a richer, safe, read-only showcase preview payload.

The publishing console should expose enough structured preview data for admin UI to display what would be reviewed for manual showcase publishing, without executing any public action.

This block should make supplier-offer rows clearer by exposing:

1. Preview title.
2. Preview body/caption summary.
3. CTA label and CTA target.
4. Media reference / media status summary.
5. Channel status summary.
6. Source of preview data.
7. Blockers/warnings from existing read-only data.
8. Safety note confirming no publish/send/schedule occurs.
9. Relationship to publish_readiness and template_library.

This is a read-only payload expansion, not a publishing implementation.

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
- docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md
- docs/HANDOFF_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT.md
- docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md
- docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md
- docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py
- app/schemas/admin_publish_readiness.py
- app/services/supplier_offer_publish_readiness.py
- app/services/admin_navigation_paths.py

If some docs do not exist, report and continue with available docs.

---

## Current foundation to preserve

Publishing console rows already include:

- `publish_readiness`
- `console_preview`
- `template_library`
- `template_kind`
- `template_version`
- `template_preview_available`
- `channel_kind`
- `channel_status`
- `actions`

B15K added/readied `template_library`.

Do not remove or break existing fields.

Prefer additive changes.

---

## Desired output

Add or refine a structured preview payload for publishing console rows, focused primarily on `supplier_offer_initial`.

Possible object name:

- `preview_payload`
- `showcase_preview_payload`
- `console_preview_payload`

Pick the least disruptive and most consistent option.

Suggested schema:

```text
preview_payload:
  payload_status: "available" | "placeholder" | "blocked" | "not_applicable"
  source: "showcase_preview" | "packaging_draft" | "supplier_offer_fields" | "tour_placeholder" | "none"
  title: str | null
  subtitle: str | null
  body_text: str | null
  caption_html: str | null
  primary_cta_label: str | null
  primary_cta_url: str | null
  secondary_cta_label: str | null
  secondary_cta_url: str | null
  media_reference: str | null
  media_status: str | null
  channel_kind: str | null
  channel_status: str | null
  channel_ref: str | null
  warnings: list[str]
  blockers: list[str]
  safety_note: str
  generated_at: datetime | null