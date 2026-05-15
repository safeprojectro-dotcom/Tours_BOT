# CURSOR_PROMPT_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- eb1473f fix: add explicit publishing editor safety flags
- e21a85f feat: add read-only publishing editor detail view
- cf28cd3 docs: add channel template editor design gate
- 5a7aa98 fix: deduplicate publishing console ui safety line
- 42a6eec feat: add publishing console admin ui metadata

Closed:
- B15 Publishing Console Foundation — closed
- B15P Admin UI read-only alignment — closed
- B17 Channel / Template Editor Design Gate — closed
- B17A Read-only Editor Detail View — closed
- B17A.1 Explicit editor safety/action flags — closed
- Railway smoke passed for `/admin/publishing-console/supplier-offers/12/editor`

Now implement:

# B17B — Channel / Template Selection Metadata Only

## Goal

Add read-only channel/template selection metadata to the B17A editor detail response.

This should help a future admin frontend render:

- available channel options
- recommended channel
- selected/current channel projection
- available template options
- recommended template
- selected/current template projection
- disabled reasons
- future-only capabilities
- safety copy around selection and publish boundaries

This is **metadata only**.

No channel selection is persisted.
No template selection is persisted.
No draft copy is edited.
No publish action is executed.
No Telegram API call is made.

---

## Critical boundary

Do NOT publish.
Do NOT send Telegram messages.
Do NOT retry Telegram messages.
Do NOT schedule publish.
Do NOT implement auto-publish.
Do NOT create publish attempts.
Do NOT execute prepare_conversion_chain.
Do NOT mutate supplier offers, tours, bridges, execution links, orders, payments, reservations, seats, content items, or drafts.
Do NOT create migration.
Do NOT change Mini App routing.
Do NOT change B11 deep-link behavior.
Do NOT introduce provider/Telegram API calls.
Do NOT add POST/PATCH endpoints.
Do NOT add frontend implementation.
Do NOT persist channel selection.
Do NOT persist template selection.

No public side effects.

---

## Required references

Inspect and align with:

- docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md
- docs/HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md
- docs/CHAT_HANDOFF.md
- docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py
- app/api/routes/admin.py
- tests/unit/test_admin_publishing_console.py

If some docs do not exist, report and continue with available docs.

---

## Existing foundation to preserve

Do not remove or rename existing fields.

Preserve:
- `GET /admin/publishing-console/supplier-offers/{offer_id}/editor`
- `channel_section`
- `template_section`
- `preview_section`
- `cta_section`
- `media_section`
- `readiness_section`
- `safety_section`
- `future_actions`
- `source_snapshot`
- all B17A.1 explicit flags

Reuse:
- `template_library.available_templates`
- existing `channel_actions`
- existing `template_actions`
- existing `channel_kind/channel_status/channel_ref`
- existing preview payload channel fields
- existing template family/selected/recommended ids

---

## Desired additions

Add additive read-only metadata to the existing editor detail response.

Preferred names:

```text
channel_selection
template_selection