# CURSOR_PROMPT_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- 30411b5 docs: close publishing console foundation
- 941d531 feat: add publishing console supplier offer detail view
- b38dad7 feat: add supplier offer showcase preview payload
- 283e5bc feat: add publishing console template library metadata
- 6bfe7d8 feat: add publishing console preview display metadata

Closed:
- B15O — Publishing Console Foundation Closure
- B15M — supplier-offer publishing console detail read view
- B15L — supplier-offer showcase preview_payload
- B15K — template_library
- B15F2/B15F3 — console_preview
- B15I — publish_readiness UX metadata
- B15H — publish_readiness read-only metadata
- B15G — guarded auto-publish design only

Now implement:

# B15P — Admin UI Polish / Read-only Frontend Alignment

## Goal

Improve the admin-facing read-only publishing console DTOs so a future admin frontend can render clear cards, groups, labels, disabled/future actions, and safety copy without inventing UI semantics.

This is a **read-only UI alignment layer** on top of existing data:

- `publish_readiness`
- `console_preview`
- `template_library`
- `preview_payload`
- supplier-offer detail view
- action metadata

The goal is **not** to implement a frontend UI.  
The goal is to add structured read-only presentation hints and docs/tests so the frontend has a stable contract.

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
Do NOT add real channel/template editor.
Do NOT add real publish buttons that execute anything.

No public side effects.

---

## Required references

Inspect and align with:

- docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md
- docs/CHAT_HANDOFF.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW.md
- docs/HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md
- docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md
- docs/HANDOFF_B15I_PUBLISH_READINESS_SUGGEST_ONLY_UX.md
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py
- app/schemas/admin_publish_readiness.py
- app/services/supplier_offer_publish_readiness.py
- tests/unit/test_admin_publishing_console.py

If some docs do not exist, report and continue with available docs.

---

## Current foundation to preserve

Do not remove or rename existing fields.

Existing surfaces:

- `GET /admin/publishing-console`
- `GET /admin/publishing-console?kind=supplier_offer_initial`
- `GET /admin/publishing-console/supplier-offers/{offer_id}`
- `GET /admin/supplier-offers/{offer_id}/review-package`
- `GET /admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan`

Existing objects:

- `publish_readiness`
- `console_preview`
- `template_library`
- `preview_payload`
- `actions`
- `safety_summary` on detail
- `conversion_summary`
- `linked_tour_summary`
- `publication_summary`

---

## Desired B15P output

Add additive read-only admin UI presentation metadata.

Preferred object names:

For list rows:
- `ui_card`

For supplier-offer detail:
- `ui_sections`

If the existing schema style suggests different names, choose the least disruptive naming.

---

## Suggested list row object: `ui_card`

Add to `AdminPublishingConsoleItemRead` a compact object such as:

```text
ui_card:
  card_title: str | null
  card_subtitle: str | null
  status_badge: str
  status_label: str
  status_tone: "neutral" | "success" | "warning" | "danger" | "info"
  primary_line: str | null
  secondary_line: str | null
  primary_action_label: str | null
  primary_action_code: str | null
  primary_action_enabled: bool
  primary_action_kind: "safe_read" | "guarded_post" | "future" | "none"
  primary_action_path: str | null
  secondary_action_label: str | null
  secondary_action_code: str | null
  secondary_action_enabled: bool
  warning_line: str | null
  blocker_line: str | null
  safety_line: str