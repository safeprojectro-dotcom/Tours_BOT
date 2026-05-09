# HANDOFF — Media storage foundation B7.4C → B7.4D

## Project

Tours_BOT — supplier offer **durable media** pipeline.

## Step completed

**B7.4C** — conservative **implementation foundation** (config, adapter abstraction, pure eligibility, tests). **Documentation finalized** in this handoff revision.

## Checkpoint

- **B7.4A:** [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md)
- **B7.4B:** [`docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`](B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md)
- **B7.4C:** Foundation code + unit tests **merged** per product scope; **`publish_safe`** remains B7.3B **deferred** stub until **B7.4D**.

## Files changed summary (B7.4C implementation)

| Area | Path |
|------|------|
| Settings | `app/core/config.py` — `MEDIA_STORAGE_BACKEND`, `MEDIA_STORAGE_BUCKET`, `MEDIA_STORAGE_ENDPOINT_URL`, `MEDIA_STORAGE_PUBLIC_BASE_URL`, `MEDIA_STORAGE_REGION`, `MEDIA_STORAGE_ACCESS_KEY_ID`, `MEDIA_STORAGE_SECRET_ACCESS_KEY`, `MEDIA_STORAGE_MAX_BYTES`, `MEDIA_STORAGE_ALLOW_HTTPS_FETCH`; `media_storage_backend_parsed`. |
| Types | `app/core/media_storage_types.py` — `MediaStorageBackend`, `MediaSourceKind`, `StoredObject`. |
| Adapter | `app/services/media_storage/__init__.py`, `app/services/media_storage/adapter.py` — `MediaStorageAdapter` protocol, disabled + in-memory adapters, `get_media_storage_adapter()`. |
| Eligibility | `app/services/supplier_offer_media_ingestion_eligibility.py` — `classify_cover_media_reference()`, `evaluate_media_ingestion_eligibility()`. |
| Dev docs | `.env.example` — B7.4C comment block. |
| Tests | `tests/unit/test_media_storage_adapter.py`, `tests/unit/test_supplier_offer_media_ingestion_eligibility.py`. |
| Continuity | `docs/CHAT_HANDOFF.md` (B7.4C bullet); this handoff. |

## Implementation behavior (short)

- **Default** `MEDIA_STORAGE_BACKEND=disabled`: writes raise `MediaStorageDisabledError`; `object_exists` is false; no credentials read.
- **Unknown** backend string → coerced to **`disabled`** at settings parse (safe startup).
- **`memory`**: in-process dict storage; optional `MEDIA_STORAGE_PUBLIC_BASE_URL` for `public_url_for`.
- **`s3_compatible`**: `get_media_storage_adapter()` raises `MediaStorageNotImplementedError` (explicit placeholder).
- **Eligibility**: mirrors B7.4B §4; **HTTPS** sources pass only when `allow_https_source` is true (wire to `Settings.media_storage_allow_https_fetch` from future orchestration).
- **No** Telegram Bot API file download, **no** HTTP client URL fetch, **no** publish handlers call ingestion.

## Tests

Run after doc finalize (or equivalent in CI):

```bash
python -m pytest tests/unit/test_media_storage_adapter.py tests/unit/test_supplier_offer_media_ingestion_eligibility.py -q
```

## Non-goals preserved (B7.4C)

Not done: real S3/object storage client, `getFile`/download, remote URL fetch, publish integration, `publish_safe` vNext persistence, readiness rule changes, migrations, new heavy storage dependencies, Mini App, booking/payment/orders.

## Likely next steps

1. **B7.4D** — Persist/update **`publish_safe` vNext** metadata path (orchestrated, explicit); **no** auto-publish.
2. **B7.4C2** — Telegram downloader **mock** or contract-only slice **if** needed before live `getFile`.
3. **B7.4E** — Readiness **policy** if durable media becomes mandatory for some publish modes.
4. **B7.5** — Rendered branded card asset.
5. **B7.6** — Telegram **`sendPhoto`** / **`sendMediaGroup`** publish integration.

## Post-merge checklist

- No undeclared storage SDK dependencies; no migrations in this track without a dedicated prompt.
- No `getFile` or URL fetch in production paths until an approved slice.
- `git status --short` / `git diff --stat` clean for unintended files.

## References

- [`docs/HANDOFF_MEDIA_STORAGE_INGESTION_CONTRACT_B7_4B_TO_NEXT_STEP.md`](HANDOFF_MEDIA_STORAGE_INGESTION_CONTRACT_B7_4B_TO_NEXT_STEP.md)
- `docs/CURSOR_PROMPT_MEDIA_STORAGE_FOUNDATION_B7_4C.md`
- `docs/CURSOR_PROMPT_B7_4C_DOCS_FINALIZE.md`
