# HANDOFF_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL_TO_NEXT_STEP

## Status: B15F implemented (docs synced)

- **Design record:** [`docs/B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md).
- **Prompt / spec:** [`docs/CURSOR_PROMPT_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md`](CURSOR_PROMPT_B15F_PUBLISHING_CONSOLE_TEMPLATE_SOURCE_CHANNEL_READ_MODEL.md).
- **Slice:** **`GET /admin/publishing-console`** remains **read-only**. Additive **source / template / channel / media** metadata per item plus **`template_actions[]`** / **`channel_actions[]`** (**`AdminPublishingConsoleFutureCapabilityHintRead`**) for UX not built yet.
- **Code:** `app/schemas/admin_publishing_console.py`; `app/services/admin_publishing_console_service.py` (`_b15f_supplier_offer`, `_b15f_tour_promotion`, `_b15f_future_template_channel_hints`).
- **Tests passed:** **`8`** — `python -m pytest tests/unit/test_admin_publishing_console.py -q`.

## Supplier-offer semantics

- **`source_kind`** **`supplier_offer`**; showcase template metadata from **`review-package`** (**`showcase_template_preview`**, **`showcase_preview`**); preview path **`/admin/supplier-offers/{id}/showcase-preview`**.
- **Channel:** Telegram showcase channel id from settings (`telegram_offer_showcase_channel_id`).
- **Media policy:** from **`cover_media_quality_review`**, publication mode, **`cover_media_publish_blocking_reasons`** (metadata-first stance).

## Tour promotion semantics

- **`source_kind`** **`tour`**; **`template_kind`** **`tour_promotion_placeholder`**; no supplier-offer showcase channel or cover policy applied; **`template_preview_available`** **`false`**.

## Important boundary

B15F does **not** execute actions, publish, send Telegram messages, edit templates, select channels, or mutate data.

## Preserved architecture

- Review-package / packaging draft remains source of truth for supplier-offer showcase content.
- B15C exact CTA gate remains source of truth for publish safety.
- B15D readiness fields remain compatible.
- B15E action affordances remain compatible.
- Layer A and Mini App routing untouched.

## Next recommended step options

After B15F, only with **explicit** product/security/design approval:

1. **B15F2** — template editor design/read model.
2. **B15F3** — channel selector design/read model.
3. **B15E2** — explicit action execution design (console or dedicated flows).
4. **B15G** — guarded auto-publish design.
