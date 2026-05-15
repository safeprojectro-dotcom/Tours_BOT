
# HANDOFF_B17A_READ_ONLY_EDITOR_DETAIL_VIEW

## Project

Tours_BOT

## Block

**B17A** — Read-only Channel / Template Editor detail view (**closed** in-repo)

## What shipped

**Endpoint (read-only)**

- **`GET /admin/publishing-console/supplier-offers/{offer_id}/editor`**
- **404** if supplier offer does not exist (same convention as B15M detail).
- Same admin auth as other **`/admin`** routes.

**Schemas (additive)**

- **`AdminPublishingConsoleEditorDetailRead`** — editor-oriented layout: `editor_status` / `editor_status_label` / `editor_status_tone`, navigation paths, section DTOs, **`future_actions`**, **`source_snapshot`**, **`generated_at`**, **`editor_notice`**.
- Section DTOs: **`channel_section`**, **`template_section`**, **`preview_section`**, **`cta_section`**, **`media_section`**, **`readiness_section`**, **`safety_section`**.

**Aggregation**

- Reuses **`AdminPublishingConsoleService`** / existing B15 review-package-backed row build (same data as **`GET …/supplier-offers/{offer_id}`** detail).
- **`source_snapshot`** embeds: **`publish_readiness`**, **`console_preview`**, **`template_library`**, **`preview_payload`**, **`ui_card`** (from finalized list item), **`safety_summary`**.
- **`future_actions`**: merged **template** + **channel** future capability hints (metadata only; disabled where not implemented).

## Explicit non-goals (unchanged)

- **No** channel/template selection persistence.
- **No** draft copy persistence.
- **No** admin web frontend in this slice.
- **No** Telegram/provider I/O, publish attempts, scheduler, auto-publish.
- **No** **`prepare_conversion_chain`** execution from this **GET**.
- **No** Layer A mutation; **no** Mini App / B11 routing changes.
- **No** migration for B17A.

## Design alignment

- Gate doc: **[`docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md`](B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md)**

## Tests

- **`tests/unit/test_admin_publishing_console.py`** — editor 401/404 and **`test_b17a_editor_detail_read_model`**.

## Prerequisites (closed)

- **[`docs/B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md`](B17_CHANNEL_TEMPLATE_EDITOR_DESIGN_GATE.md)** (B17 design gate)
- B15 publishing console foundation, B15M detail, B15P **`ui_card`**

## Suggested next

- Optional: Railway read-only smoke for **`/editor`**.
- Product: **B17B** — channel/template selection **metadata** persistence only (separate charter) — **not** Telegram publish without explicit go/no-go.

## Related

- Prompt: [`docs/CURSOR_PROMPT_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md`](CURSOR_PROMPT_B17A_READ_ONLY_EDITOR_DETAIL_VIEW.md)
