# CURSOR_PROMPT_B15F2F3_PUBLISHING_CONSOLE_TEMPLATE_PREVIEW_REFINEMENT

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- f63244 docs: record publish readiness suggest-only smoke
- 06cc17 feat: add publish readiness suggest-only display metadata
- 48c65cf docs: record publish readiness read-only smoke
- 30321e9 feat: add read-only publish readiness metadata
- d3db31 docs: design guarded auto publish gates

Closed:
- B15G — guarded auto-publish design only
- B15H — read-only publish readiness metadata
- B15H smoke — Railway read-only smoke passed
- B15I — suggest-only display metadata
- B15I smoke — Railway read-only smoke passed

Now implement:

# B15F2/B15F3 — Publishing Console Template / Preview Refinement

## Critical boundary

This is READ-ONLY publishing console refinement.

Do NOT publish.
Do NOT send Telegram messages.
Do NOT retry Telegram messages.
Do NOT schedule publish.
Do NOT implement auto-publish.
Do NOT create publish attempts.
Do NOT execute prepare_conversion_chain.
Do NOT mutate supplier offers, tours, bridges, execution links, orders, payments, reservations, or seats.
Do NOT create migration.

---

## Goal

Improve publishing console read models so admin can see a clearer template/preview layer for publishing candidates.

The console should help admin understand:

1. What type of candidate this is:
   - supplier_offer_initial
   - tour_promotion
   - future campaign/promo candidate if already represented

2. Which template family applies:
   - supplier offer showcase
   - tour promotion placeholder
   - custom request CTA / per-seat / full-bus where current data supports it

3. Whether preview is available now:
   - available
   - placeholder only
   - blocked
   - not applicable

4. What admin can safely do next:
   - review package
   - review publish readiness
   - review template preview
   - compose later / not implemented
   - do nothing because already published

5. Why no public action is taken.

This is a read-model/UX clarity step, not an execution step.

---

## Required references

Inspect and align with:

- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md
- docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md
- docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md
- docs/B15H_READ_ONLY_PUBLISH_READINESS_SMOKE.md
- docs/B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX_SMOKE.md
- docs/CHAT_HANDOFF.md
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py
- app/schemas/admin_publish_readiness.py
- app/services/supplier_offer_publish_readiness.py
- app/services/admin_navigation_paths.py

---

## Current situation to preserve

Publishing console currently has rows such as:

- supplier_offer_initial rows
- tour_promotion rows

B15H/B15I added `publish_readiness`.

Tour promotion rows currently have:
- template_kind: tour_promotion_placeholder
- template_version: not_implemented
- template_preview_available: false
- channel_kind: none
- channel_status: not_applicable
- actions such as compose_tour_promotion_draft disabled/future

This is acceptable and must not be turned into real publish behavior in this block.

---

## Desired read-model improvements

Add or refine a compact `template_preview` / `publish_preview` / `console_preview` object, depending on existing naming style.

Prefer not to break existing fields. Additive fields are preferred.

Example shape:

```text
console_preview:
  preview_status: "available" | "placeholder" | "blocked" | "not_applicable"
  template_family: "supplier_offer_showcase" | "tour_promotion" | "custom_request_cta" | "unknown"
  template_id: optional string
  template_version: optional string
  title: optional string
  summary: optional string
  primary_cta_label: optional string
  target_kind: optional string
  target_url: optional string
  media_status: optional string
  channel_status: optional string
  preview_path: optional string
  safety_note: string
  next_action_code: optional string
  next_action_label: optional string