# CURSOR_PROMPT_B17A_READ_ONLY_EDITOR_DETAIL_VIEW

You are continuing the existing Tours_BOT project.

This is NOT a new project and NOT a rewrite.

Current clean checkpoints:

- cf28cd3 docs: add channel template editor design gate
- 5a7aa98 fix: deduplicate publishing console ui safety line
- 42a6eec feat: add publishing console admin ui metadata
- 30411b5 docs: close publishing console foundation
- 941d531 feat: add publishing console supplier offer detail view

Closed:
- B15 Publishing Console Foundation — closed
- B15P Admin UI read-only alignment — closed
- B15P.1 safety-line polish — closed
- B17 Channel / Template Editor Design Gate — closed as docs-only

Now implement:

# B17A — Read-only Channel / Template Editor Detail View

## Goal

Add a read-only admin editor detail view for a supplier-offer publishing candidate.

This endpoint should aggregate existing B15/B17 read-model data into an editor-oriented view so a future admin frontend can render:

- channel section
- template section
- preview section
- CTA section
- media section
- readiness section
- safety section
- future action section

This is NOT a real editor implementation.

No channel/template selection is persisted.
No draft text is edited.
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
Do NOT mutate supplier offers, tours, bridges, execution links, orders, payments, reservations, seats, or content items.
Do NOT create migration.
Do NOT change Mini App routing.
Do NOT change B11 deep-link behavior.
Do NOT introduce provider/Telegram API calls.
Do NOT add real channel/template editor mutation.
Do NOT add POST/PATCH endpoints.
Do NOT add scheduler.
Do NOT add frontend implementation.

No public side effects.

---

## Required references

Inspect and align with:

- docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md
- docs/CHAT_HANDOFF.md
- docs/B15O_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE.md
- docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/HANDOFF_B15P_ADMIN_UI_READ_ONLY_ALIGNMENT.md
- docs/HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW.md
- docs/HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md
- docs/HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md
- app/schemas/admin_publishing_console.py
- app/services/admin_publishing_console_service.py
- app/api/routes/admin.py
- tests/unit/test_admin_publishing_console.py

If some docs do not exist, report and continue with available docs.

---

## Existing foundation to reuse

Do not duplicate business logic.

Reuse existing service/read-models:

- `AdminPublishingConsoleService.read_supplier_offer_detail`
- supplier-offer detail read model
- `publish_readiness`
- `console_preview`
- `template_library`
- `preview_payload`
- `ui_card`
- `safety_summary`
- `conversion_summary`
- `linked_tour_summary`
- `publication_summary`
- existing action metadata

Do not remove, rename, or alter existing fields.

---

## Desired endpoint

Add a read-only admin endpoint:

`GET /admin/publishing-console/supplier-offers/{offer_id}/editor`

Response model suggestion:

`AdminPublishingConsoleEditorDetailRead`

This endpoint must use the same admin auth dependency as other `/admin` routes.

Missing offer:
- return 404 using existing project conventions.

---

## Desired response structure

Create additive schemas in `app/schemas/admin_publishing_console.py`.

Suggested top-level response:

```text
supplier_offer_id: int
candidate_key: str
kind: "supplier_offer_initial"
title: str | null
editor_status: str
editor_status_label: str
editor_status_tone: "neutral" | "success" | "warning" | "danger" | "info"

source_detail_path: str
review_package_path: str
publishing_console_detail_path: str
prepare_conversion_chain_plan_path: str | null

channel_section: ...
template_section: ...
preview_section: ...
cta_section: ...
media_section: ...
readiness_section: ...
safety_section: ...
future_actions: list[...]

source_snapshot:
  publish_readiness: AdminPublishReadinessRead
  console_preview: AdminPublishingConsolePreviewRead
  template_library: AdminPublishingConsoleTemplateLibraryRead
  preview_payload: AdminPublishingConsolePreviewPayloadRead
  ui_card: AdminPublishingConsoleUiCardRead
  safety_summary: existing detail safety summary if available

generated_at: datetime