# HANDOFF_B15M_PUBLISHING_CONSOLE_SUPPLIER_OFFER_DETAIL_READ_VIEW

## Project

Tours_BOT

## Block

**B15M — Admin Publishing Console Supplier-offer Detail Read View** (closed in-repo, docs continuity)

## Delivered

**Read-only admin detail endpoint**

- `GET /admin/publishing-console/supplier-offers/{offer_id}`

**Response model**

- `AdminPublishingConsoleSupplierOfferDetailRead` — aggregates the same publishing-console read surfaces as list rows, plus structured summaries for OPS.

**Service**

- `AdminPublishingConsoleService.read_supplier_offer_detail(session, offer_id=...)`

**Aggregates (all read-only, derived from existing review-package / console builders)**

- `publish_readiness` (`AdminPublishReadinessRead`)
- `console_preview` (`AdminPublishingConsolePreviewRead`)
- `template_library` (`AdminPublishingConsoleTemplateLibraryRead`)
- `preview_payload` (`AdminPublishingConsolePreviewPayloadRead`)
- `actions`, path metadata (`review_package_path`, `prepare_conversion_chain_plan_path`, `publish_action_path`, `prepare_conversion_chain_action` affordance)
- `conversion_summary`, `linked_tour_summary`, `publication_summary`
- `safety_summary` (explicit flags: read-only, no Telegram I/O, no publish attempt, no prepare-chain execution, no Layer A mutation)
- `generated_at`, `detail_notice`

**Queue vs detail**

- Detail is available for **any existing** supplier offer id (404 if missing). Offers **omitted** from the publishing-console **list** queue (e.g. list filter for fully published rows with no missing step) may **still** be fetched by this detail route.

**Auth / errors**

- Same **`/admin`** router dependency as other admin routes (admin API token).
- Unknown `offer_id` → **404**.

## Must not happen (preserved)

- Telegram publish / send / retry
- Scheduler / auto-publish
- Publish attempt creation
- `prepare_conversion_chain` **execution** from this GET (B15E2/B16D2C POST remains separate)
- Bridge / tour / execution-link / order / payment / reservation / seat mutation
- Mini App / B11 routing changes
- Migration

## Related docs

- Foundation checkpoint: [`docs/B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md`](B15_PUBLISHING_CONSOLE_FOUNDATION_CLOSURE_CHECKPOINT.md)
- Chat handoff: [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)

## Suggested next

- Optional: short **read-only** smoke on deployed admin (`GET …/supplier-offers/{id}` with token, 404 on bogus id)
- Then product choice: admin UI detail polish, template/channel editor gate, or deeper read-only fields — **no** public publish automation without separate go/no-go
