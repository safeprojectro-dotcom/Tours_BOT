# CURSOR_PROMPT_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 48c65cf docs: record publish readiness read-only smoke
- 30321e9 feat: add read-only publish readiness metadata
- d3db31 docs: design guarded auto publish gates
- 81b65c5 docs: record publishing console prepare chain smoke
- aa1dc8 feat: add publishing console prepare chain action execution

Closed:
- B15G — guarded auto-publish design only
- B15H — read-only publish readiness metadata
- B15H smoke — Railway read-only smoke passed

Now implement:

# B15I — Suggest-only UX / Read-model refinement for publish_readiness

## Critical boundary

This is READ-ONLY UX/read-model refinement.

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

Make existing `publish_readiness` easier for admin/OPS consumers to understand by adding concise suggest-only read fields.

B15H already exposes detailed gate metadata.

B15I should add a compact human-readable summary layer such as:

- publish_readiness_summary
- publish_readiness_badge
- publish_readiness_next_action_code
- publish_readiness_next_action_label
- publish_readiness_primary_blocker
- publish_readiness_warning_summary
- publish_readiness_gate_summary

Exact naming may follow existing project style.

The purpose is to help admin UI/console display:
- already published
- ready to suggest manual publish
- needs review
- blocked
- not applicable

without parsing the full gates array.

---

## Required references

Inspect and align with:

- docs/B15G_GUARDED_AUTO_PUBLISH_DESIGN.md
- docs/B15H_READ_ONLY_PUBLISH_READINESS_SMOKE.md
- docs/HANDOFF_B15H_READ_ONLY_PUBLISH_READINESS.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/CHAT_HANDOFF.md
- app/schemas/admin_publish_readiness.py
- app/services/supplier_offer_publish_readiness.py
- app/schemas/supplier_admin.py
- app/schemas/admin_publishing_console.py
- app/services/supplier_offer_review_package_service.py
- app/services/admin_publishing_console_service.py

---

## Desired metadata shape

Prefer extending `AdminPublishReadinessRead` itself if that is clean.

Example fields:

- `summary: str`
- `badge: str`
  - examples:
    - `already_published`
    - `ready_to_suggest`
    - `needs_review`
    - `blocked`
    - `not_applicable`

- `next_action_code: str | None`
  - examples:
    - `review_conversion_health`
    - `manual_publish_available`
    - `resolve_publish_blockers`
    - `review_warnings`
    - `not_applicable`

- `next_action_label: str | None`
  - human-readable admin text

- `primary_blocker: str | None`
  - first failed blocker reason if any

- `warning_summary: str | None`
  - compact warning count/reason summary

- `gate_summary: str | None`
  - compact “passed X / failed Y / warnings Z”

If project style prefers a nested object, use for example:
`publish_readiness_ux: AdminPublishReadinessUxRead` — **B15I** instead **extends `AdminPublishReadinessRead` in place** (single DTO).

