# HANDOFF_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD

## Project

Tours_BOT

## Block

**B15L** — Supplier-offer showcase **preview payload** on the admin publishing console (read-only)

## Delivery summary

Every **`GET /admin/publishing-console`** item includes additive **`preview_payload`** (`AdminPublishingConsolePreviewPayloadRead`).

### Schema (`app/schemas/admin_publishing_console.py`)

- **`PublishingConsolePreviewPayloadStatus`** — `available` | `placeholder` | `blocked` | `not_applicable`
- **`PublishingConsolePreviewPayloadSource`** — `showcase_preview` | `packaging_draft` | `supplier_offer_fields` | `tour_placeholder` | `none`
- **`AdminPublishingConsolePreviewPayloadRead`**
- **`AdminPublishingConsoleItemRead.preview_payload`**

### Supplier-offer rows (`supplier_offer_initial`)

Built from the same **read-only review-package** snapshot as the console row:

- **`showcase_preview`**: `caption_html`, CTA hrefs, showcase photo URL, publication mode, merged warnings
- **Supplier-offer fields**: title/subtitle context, plain **`body_text`** (HTML stripped from caption when present, else marketing/description/program fallback)
- **Template / channel / media** (from existing B15F fields on the row): reflected in **`payload_status`**, channel fields, and **`media_status`**

Includes **`publish_readiness_note`** and **`template_library_note`** — short strings tying this object to the same item’s **`publish_readiness`** and **`template_library`** (no extra I/O).

### Tour-promotion rows

- **`payload_status`**: **`not_applicable`**
- **`source`**: **`tour_placeholder`**
- Placeholder copy only; no supplier showcase caption pipeline

### Safety (no public side effects)

**No** Telegram I/O, publish attempts, scheduler, auto-publish, **`prepare_conversion_chain`** execution, Layer A mutation, Mini App/B11 routing changes, migration, or provider/Telegram API calls from this projection.

### Tests

**`tests/unit/test_admin_publishing_console.py`** covers **`preview_payload`** (see repo for current pass count).

## Next (optional)

- Short read-only Railway smoke: spot-check **`preview_payload`** on supplier vs tour rows
- Further UI/copy or editor slices only under explicit charter — **not** automatic public publish

## References

- **[`docs/CURSOR_PROMPT_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md`](CURSOR_PROMPT_B15L_SUPPLIER_OFFER_SHOWCASE_PREVIEW_PAYLOAD.md)**
- **[`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md)**
- **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)**
