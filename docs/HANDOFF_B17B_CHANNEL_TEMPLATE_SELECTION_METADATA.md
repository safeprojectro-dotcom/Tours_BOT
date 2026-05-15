# HANDOFF_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA

## Project

Tours_BOT

## Block

**B17B** — Channel / Template Selection **Response Metadata** (read-only editor GET)

## What shipped

**Endpoint (unchanged route, extended response)**

- **`GET /admin/publishing-console/supplier-offers/{offer_id}/editor`**
- Additive JSON fields only: **`channel_selection`**, **`template_selection`** on **`AdminPublishingConsoleEditorDetailRead`**.
- **No** new routes. **No** POST/PATCH. **No** DB persistence. **No** migration.

**`channel_selection` (read-only metadata)**

- **`available_options`** — MVP-oriented rows (e.g. Telegram showcase + read-model placeholder).
- **`current_projection`** — mirrors the console row channel projection (kind, status, ref, summary).
- **`recommended_option_key`** — which option is recommended in this context.
- **`global_disabled_reason`** / per-option **`disabled_reason`** where applicable.
- **`selection_safety_note`** — boundary copy (GET-only; no persistence).
- **`future_capability_hints`** — same hints as **`channel_actions`** (e.g. `select_channel`), metadata only.
- **`payload_mirror_note`** — when **`preview_payload`** channel fields diverge from the row projection.

**`template_selection` (read-only metadata)**

- **`available_options`** — aligned with **`template_library.available_templates`** (`is_recommended`, `is_current_projection`, status, disabled reasons).
- **`current_projection`** — consolidated template/family/summary/selection reason; optional **`projection_align_note`** when console vs library ids differ.
- **`recommended_template_id`**, **`selected_template_id`**, **`console_preview_template_id`**.
- **`global_disabled_reason`**, **`selection_safety_note`**, **`future_capability_hints`** (same as **`template_actions`**).

**Explicit non-goals (verified for this slice)**

- **B17B exposes response metadata only on the read-only editor GET; it does not persist channel selection, template selection, draft edits, or editor state.**
- **No** admin web frontend implementation in this slice.
- **No** Telegram / provider I/O, publish attempts, scheduler, auto-publish.
- **No** **`prepare_conversion_chain`** execution from this **GET**.
- **No** Layer A mutation; **no** Mini App / B11 routing changes.

## Tests

Focused publishing-console suite (as run after implementation): **41 passed**, **1** existing SQLAlchemy **SAWarning** (test harness; unchanged).

## Design alignment

- **[`docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md`](B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md)** (B17B record + B17C+ gate for persistence/publish).
- **[`docs/HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md`](HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md)** (B17A + B17A1 + B17B handoff notes).

## Related

- Prompt: [`docs/CURSOR_PROMPT_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md`](CURSOR_PROMPT_B17B_CHANNEL_TEMPLATE_SELECTION_METADATA.md)
