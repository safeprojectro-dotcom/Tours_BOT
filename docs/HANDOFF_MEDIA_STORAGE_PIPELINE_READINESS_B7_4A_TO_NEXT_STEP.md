# HANDOFF — Media storage pipeline readiness B7.4A → B7.4B

## Project

Tours_BOT — supplier offer **media storage pipeline** (publish-safe durability).

## Current checkpoint

- **C2B8B:** Telegram showcase publish gated; media blockers can disable publish via review-package / operator_workflow.
- **C2B10T-A/B/C:** Telegram conversion chain (link tour, list for sale, publish, booking link) in place.
- **B7.3B:** `publish_safe` **metadata-only** stub in `packaging_draft_json` (`status: deferred`, `object_key` / `public_url` **null**); source reference may be `telegram_photo:{file_id}` or URL-like text.

## Audit summary (B7.4A)

- Documented in [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md).
- **Current pipeline is metadata-only:** no durable object key, no canonical public URL in `publish_safe`, no mandatory byte ingest.
- **Gaps vs publish-safe storage:** reliance on ephemeral Telegram references for optional `sendPhoto`; no app-owned blob lifecycle.
- **Direction:** S3-compatible (or equivalent) object storage when scoped; phased B7.4B–B7.6 rollout; readiness tightening (B7.4E) only if policy demands a durable asset.

## Next recommended step

**B7.4B — Media storage ingestion contract / design doc** (interfaces, failure modes, idempotency, mapping into `publish_safe` fields). No production storage access or Telegram download required for the doc itself.

## Non-goals preserved (until explicitly scoped)

- Do not break media review, OK photo, or request replacement flows.
- Do not loosen publish readiness; review-package / operator_workflow stay authoritative.
- Do not implement booking, payment, or orders in this track.
- Do not require Mini App changes for media storage MVP.
- **B7.4A was docs-only:** no app code, no migrations, no production storage access, no real Telegram file download.

## Implementation sequence after B7.4B (reference)

B7.4B (contract/design) → B7.4C (config + adapter/service + tests, no auto-publish) → B7.4D (durable metadata in `publish_safe`) → B7.4E (readiness integration if required) → B7.5 (branded card asset) → B7.6 (Telegram `sendPhoto` / `sendMediaGroup` integration details).
