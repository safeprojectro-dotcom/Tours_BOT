# HANDOFF — Publish safe vNext metadata B7.4D → next

## Project

Tours_BOT — supplier offer **`publish_safe`** / durable media pipeline.

## Step completed (docs finalize sync)

**B7.4D** — **`publish_safe` vNext** metadata helpers in `app/services/supplier_offer_publish_safe_vnext.py` (finalize doc revision).

## Checkpoint

| Prior | Status |
|-------|--------|
| B7.4A–B7.4C | See earlier handoffs (audit, contract, storage foundation). |
| **B7.4D** | vNext **states** (`deferred`, `pending`, `ready`, `failed`, `blocked`), **`B7_4D_VERSION`**, **fingerprint**, **review_snapshot** normalization, **merge** (only `publish_safe`), **builders**, **drift → blocked**, **`mark_publish_safe_ready`**, **deferred compat** helper. |

## Files summary (B7.4D slice)

| Path | Role |
|------|------|
| `app/services/supplier_offer_publish_safe_vnext.py` | vNext API (uses `StoredObject`, reuses B7.3B stub constants where needed). |
| `tests/unit/test_supplier_offer_publish_safe_vnext.py` | Unit tests (shapes, merge, drift, `mark_publish_safe_ready`, deferred compat). |

**Unchanged by B7.4D:** publish handlers, readiness gates, `SupplierOfferMediaReviewService`, migrations, Mini App, orders.

## Behavior summary

- **Merge** returns a **new** `packaging_draft_json` dict with **only** `publish_safe` replaced; other keys preserved by shallow copy.
- **Helpers** do **not** assign to the ORM row or mutate **`media_review`**, **`cover_media_reference`**, or lifecycle — callers commit merged draft when appropriate.
- **`publish_safe_apply_hero_drift_block`:** if `publish_safe.status == ready` and hero / stored snapshot / `media_review` snapshot diverge → **`blocked`**, clears `object_key` / `public_url`, sets drift error codes.
- **No** byte ingest, **no** `getFile`, **no** S3 upload, **no** URL fetch, **no** Telegram publish wiring.

## Tests run (finalize verification)

```bash
python -m pytest tests/unit/test_supplier_offer_publish_safe_vnext.py -q
python -m pytest tests/unit/test_supplier_offer_b7_1_media_review.py -q
```

## Non-goals preserved

No Telegram download, no real storage upload, no remote URL fetch, no publish integration, no publish readiness behavior changes, no migrations, no `media_review` mutation in these helpers, no Mini App / booking / payment / order work.

## Next options (product priority)

1. **B7.4E** — Policy / readiness integration **design** (or implementation) if durable **`publish_safe.ready`** must gate some publish modes.
2. **B7.4C2** — Telegram **downloader** mock or contract-only foundation.
3. **B7.5** — Rendered branded card asset.
4. **B7.6** — Telegram **`sendPhoto`** / **`sendMediaGroup`** publish.

## References

- [`docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`](B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md)
- [`docs/HANDOFF_MEDIA_STORAGE_FOUNDATION_B7_4C_TO_NEXT_STEP.md`](HANDOFF_MEDIA_STORAGE_FOUNDATION_B7_4C_TO_NEXT_STEP.md)
- `docs/CURSOR_PROMPT_PUBLISH_SAFE_VNEXT_METADATA_B7_4D.md`
- `docs/CURSOR_PROMPT_B7_4D_DOCS_FINALIZE.md`
