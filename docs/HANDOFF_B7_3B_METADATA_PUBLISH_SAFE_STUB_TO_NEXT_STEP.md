# HANDOFF_B7_3B_METADATA_PUBLISH_SAFE_STUB_TO_NEXT_STEP

Project: Tours_BOT

## Current checkpoint (after B7.3B)

B7.3A media policy remains accepted and documented (raw ≠ publish-safe, `file_id` ≠ public URL, `approved_for_card` ≠ `publish_safe` ≠ published, no Railway FS as canonical store, future S3-compatible storage when scoped).

**B7.3B shipped (metadata only):** `packaging_draft_json.publish_safe` is written when B7.1 media review actions run or B7.2 card render preview is persisted. Stub fields include `status: deferred`, `reason: no_durable_media_storage`, `storage_kind: none`, null `object_key` / `public_url`, `source_media_reference`, `expected_future_storage`, `marked_at` / `marked_by`, `version: b7_3b`. Implementation: `app/services/supplier_offer_publish_safe_stub.py`, merged from `supplier_offer_media_review_service` and `supplier_offer_card_render_preview`.

**Caveat:** `GET /admin/.../media/review` does not backfill `publish_safe` for rows that never received a B7.1 write or B7.2 generate after B7.3B; the stub appears on the next such write, or use optional B7.3C-style read-path materialization if ops needs it.

## Goal of B7.3B (achieved)

Add metadata-only `publish_safe` stub in Supplier Offer packaging/media metadata.

Expected behavior (met):

- Telegram-only / pipeline state → `publish_safe.status = deferred`.
- `public_url` remains null.
- `storage_kind = none`.
- No Telegram download, S3, card rendering, sendPhoto, Mini App, or booking/payment changes.

## Still future

- real Telegram getFile/download
- durable object storage
- public URL lifecycle
- real card rendering
- sendPhoto/sendMediaGroup
- B11 deep-link routing
- B10.6 bot router/consultant redesign
- B12/B13 template/channel adapters

## Next safe options (choose explicitly; do not start automatically)

1. B11 — Telegram deep-link routing to exact Tour/Mini App landing.
2. B10.6 — Telegram bot router/consultant redesign.
3. B12/B13 — marketing template library / channel adapters.
4. B7.4 — storage abstraction design/implementation if object storage policy is selected.
5. B7.3C — admin read visibility / backfill for `publish_safe` if ops needs it on GET without a write.

Do not start any next step automatically.
