# HANDOFF_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER

## Project

Tours_BOT

## Block

**B15K** — Publishing Console Template Library / Preview Layer (read-only)

## Delivery summary

**`GET /admin/publishing-console`** each item now includes additive **`template_library`** (`AdminPublishingConsoleTemplateLibraryRead`): possible variants, selected/recommended ids, version hint, **`selection_reason`**, and per-variant rows with status + **`disabled_reason`**. **`console_preview`** (B15F2/B15F3) remains; it is **not** replaced.

### Schema (`app/schemas/admin_publishing_console.py`)

- **`PublishingConsoleTemplateLibraryFamily`** — `supplier_offer_showcase` | `tour_promotion` | `unknown`
- **`PublishingConsoleTemplateLibraryEntryStatus`** — `available` | `future` | `not_applicable` | `blocked`
- **`AdminPublishingConsoleTemplateLibraryEntryRead`**
- **`AdminPublishingConsoleTemplateLibraryRead`**
- **`AdminPublishingConsoleItemRead.template_library`** (required on console items)

### Row behavior

- **`supplier_offer_initial`**: library **`family`** reflects supplier-offer showcase track; **`supplier_offer_showcase`** vs **`custom_request_cta`** appear in **`available_templates`** where applicable (assisted-closure offers prioritize **`custom_request_cta`**).
- **`tour_promotion`**: placeholder/read-only; variants are **`future`** (e.g. placeholder + rich-card sketch). **`family`** = **`tour_promotion`**.

### Safety (no public side effects)

- **No** Telegram I/O, publish attempts, scheduler, auto-publish, **`prepare_conversion_chain`** execution from this slice
- **No** Layer A mutation
- **No** Mini App / B11 routing changes
- **No** migration

### Tests

**`tests/unit/test_admin_publishing_console.py`** — asserts **`template_library`** on smoke, tour-only, and supplier showcase-ready scenarios (see repo for current pass count).

## Prerequisites (context)

Earlier console slices: B15B–B15F, B15F2/B15F3 (`console_preview`), B15H/B15I (`publish_readiness`), B15E2 (separate POST for prepare-chain).

## Next (product / ops)

- Optional read-only Railway smoke: confirm **`template_library`** on supplier and tour rows in a deployed env.
- Further work (explicit charter only): expand read-only library, admin copy, or template/channel **editor** design — **not** automatic public publish.

## References

- **[`docs/CURSOR_PROMPT_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md`](CURSOR_PROMPT_B15K_PUBLISHING_CONSOLE_TEMPLATE_LIBRARY_PREVIEW_LAYER.md)** (prompt)
- **[`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md)**
- **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)**
