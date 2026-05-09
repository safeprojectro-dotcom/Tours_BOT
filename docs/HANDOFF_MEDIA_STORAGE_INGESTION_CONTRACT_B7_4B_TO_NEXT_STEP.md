# HANDOFF — Media storage ingestion contract B7.4B → B7.4C

## Project

Tours_BOT — supplier offer **durable media ingestion** (publish-safe track).

## Step completed

**B7.4B** — ingestion **contract / design** (docs only).

**Primary artifact:** [`docs/B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md`](B7_4B_MEDIA_STORAGE_INGESTION_CONTRACT.md)

## Current checkpoint

- **B7.4A:** Readiness audit — [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md).
- **B7.4B:** Ingestion contract **saved**; **`publish_safe`** remains **stub / deferred** in runtime until **B7.4D+**.
- **Runtime:** No durable bytes, no object storage adapter in app, no **`getFile`** **/** download paths, no production bucket wiring.

## Summary of B7.4B design decisions

As documented in the contract:

1. **Source types** — `telegram_photo:{file_id}` (ingest after Bot API pipeline exists); `https://` copy-to-storage **if** policy allows outbound fetch; `http://` default **blocked**; empty **never** ingested; unknown schemes **blocked** until added to contract.
2. **Eligibility** — Requires non-empty **`cover_media_reference`**, **`media_review.status == approved_for_card`**, **no** snapshot drift vs **`media_review.cover_media_reference`**, supported source, **explicit** trigger (no hidden ingest on publish by default); aligns with **C2B8A** **/** **C2B7.2a** trust model.
3. **Storage adapter** — Narrow **`MediaStorageAdapter`**-style abstraction (`put_object`, `object_exists`, `public_url_for`, optional `delete_object`); tests use **fake** **/** mock.
4. **Telegram** — **`getFile`** → **`file_path`** → HTTPS download; caps and errors documented; **not** executed until an approved implementation slice.
5. **Object keys** — Prefix + offer identity + content hash **/** versioning per **B7.4D**; idempotency via stable keys **/** `publish_safe` readiness checks.
6. **`publish_safe` vNext** — Transition from **`deferred`** to **ready** **/** **failed** with **`object_key`**, **`public_url`** **or** signed-URL policy, integrity fields; stale on hero change.
7. **Publish readiness** — **Additive** optional **B7.4E** gate only with product sign-off; **must not** weaken existing media **/** operator gates.
8. **Security, config, and testing** — Env-driven flags, max bytes, no secrets in `publish_safe`, least-privilege IAM; B7.4C starts with pure eligibility logic, adapter mock, and unit tests.

## Non-goals (preserved from B7.4B)

B7.4B did **not** introduce: app code, tests, migrations, storage dependencies, real Telegram download, real storage access, publish behavior changes, Mini App work, or booking **/** payment **/** orders.

## Recommended B7.4C scope (conservative foundation)

- **Config settings only** — feature flag(s), optional bucket **/** prefix placeholders, limits (e.g. max download bytes), **no** hardcoded production ARNs **/** hostnames.
- **Storage adapter interface** — protocol **/** ABC as in contract; **no** mandatory boto3 wiring in the first merge if the prompt keeps deps minimal.
- **Local/mock adapter** — in-memory or temp-dir for unit tests.
- **Ingestion eligibility** (pure functions or thin service) — single module callable from future orchestration; mirrors contract §4.
- **Tests** — eligibility matrix, adapter fake, **no** live network.
- **No** real **`getFile`** **/** Telegram file download **unless** a dedicated prompt explicitly approves it.
- **No** publish integration (showcase **/** admin confirm) yet.
- **No** DB migrations **unless** a **later** approved prompt proves unavoidable (default: **none** in B7.4C).

## Review checklist before and during B7.4C merge

- No hidden ingestion on **read** paths.
- No hidden ingestion on **publish** **/** confirm.
- No bypass of **`media_review`**.
- No weakening **C2B8A** (or related) gates.
- Source **/** snapshot **drift** invalidates durable readiness (same as contract).
- No production bucket or vendor assumptions baked into defaults.
- Dependencies: **no** new storage client libraries **until** explicitly justified by the B7.4C prompt.

## References

- [`docs/HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md`](HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md)
- `docs/CURSOR_PROMPT_MEDIA_STORAGE_INGESTION_CONTRACT_B7_4B`
- `docs/CURSOR_PROMPT_B7_4B_HANDOFF_FINALIZE.md`
