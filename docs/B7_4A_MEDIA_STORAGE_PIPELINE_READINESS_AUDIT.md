# B7.4A — Media storage pipeline readiness audit

**Status:** docs-only audit (2026-05). No implementation in this step.

## 1. Scope and non-goals

**In scope**

- How supplier-offer cover and showcase media are represented today (DB fields and `packaging_draft_json`).
- How media moves from intake through review, publish-safe stub, readiness gates, and Telegram showcase send paths — **without** assuming durable object storage exists.
- Gaps relative to a **publish-safe, durable** asset (stable object key / public URL or equivalent) suitable for long-lived channel posts.
- A **proposed** storage direction and a **phased** implementation order (B7.4B–B7.6) that preserves existing safety gates.

**Explicit non-goals (this audit and checkpoint)**

- No application code changes.
- No database migrations.
- No Mini App changes.
- No booking, payment, or orders changes.
- No loosening or refactoring of publish readiness behavior (review-package / operator_workflow remain authoritative).
- No live Telegram `getFile` or byte download.
- No access to production object storage or production media buckets.

---

## 2. Document inventory inspected

The B7.4A prompt called for read-only review of project docs (presence may vary per checkout):

- `docs/CHAT_HANDOFF.md`
- `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`
- `docs/SUPPLIER_OFFER_TO_TOUR_BRIDGE_READINESS_C2B9A.md`
- `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`
- `docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`
- B7.3 / B7.4 prompts and handoffs (e.g. `docs/CURSOR_PROMPT_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A.md`, `docs/HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md`)
- Media / showcase design notes as referenced from handoff (e.g. photo moderation and card generation design docs)

Code paths were consulted **read-only** for factual alignment (e.g. `publish_safe` stub shape, showcase builder). No code was modified for B7.4A.

---

## 3. Current media data model

**`SupplierOffer` (representative)**

- **`cover_media_reference`** — string reference to supplier/source cover (may be `telegram_photo:{file_id}` or URL-like text depending on intake).
- **`showcase_photo_url`** — optional column; quality review compares it to `cover_media_reference` when both set (avoid drift for showcase preview/publish).
- **`packaging_draft_json`** — JSON bag containing workflow state, including:
  - **`media_review`** — snapshot-style fields (e.g. `cover_media_reference`, review status, moderation snapshot) used by review and readiness layers.
  - **`card_render_preview`** (B7.2) — structured preview JSON, not stored image bytes.
  - **`publish_safe`** (B7.3B stub) — **metadata-only** block merged by `merge_publish_safe_into_draft`: `status: deferred`, `storage_kind: none`, **`object_key: null`**, **`public_url: null`**, with `source_media_reference` copied from media review or row.

**Semantics (policy, unchanged by this audit)**

- **`approved_for_card` (B7.1)** is not the same as **`publish_safe`** (intended eventual durable off-Telegram asset).
- **`publish_safe`** is not the same as **`published`** (channel/showcase is an explicit admin action downstream).

---

## 4. Current media workflow end-to-end

```text
Supplier cover intake
  -> cover_media_reference (and possibly showcase_photo_url) on SupplierOffer
  -> packaging_draft_json.media_review updated via media review services
  -> Admin: OK photo / request replacement (Telegram + admin moderation paths)
  -> B7.3B: publish_safe stub merged into draft (deferred, no bytes, no URLs)
  -> Review-package + operator_workflow gates (incl. media blockers for showcase publish)
  -> build_showcase_publication: caption HTML + optional photo argument
       (Telegram file_id or HTTPS URL string — no fetch of bytes in builder)
  -> telegram_showcase_client: sendPhoto when photo string present, else sendMessage
```

**Observations**

- The pipeline is **metadata-first**: review state and references dominate; there is **no** canonical durable object store for media bytes in MVP.
- Telegram **`file_id`** can be used as the `photo` argument for `sendPhoto` without downloading, but it is **not** a stable public asset URL for long-term channel semantics or off-Telegram reuse.
- The `publish_safe` block explicitly records **deferred** durability with **`object_key` / `public_url` unset**.

---

## 5. Gaps vs durable publish-safe storage

| Area | Today | Gap for “publish-safe durable” |
|------|--------|--------------------------------|
| Bytes | Not ingested to app-controlled storage | No canonical blob; retries, CDN, compliance, and tamper-evident versioning are undefined |
| Identity | References + deferred stub | No stable **`object_key`** / **`public_url`** (or signed URL policy) in `publish_safe` |
| Lifecycle | `file_id` / raw refs | Telegram file IDs can expire or drift; not a contract for marketing archive |
| Readiness | Review-package / operator_workflow | Future policy may require “durable asset present” — **not** enforced today beyond metadata stub |
| Showcase | Optional `sendPhoto` with string | No guaranteed path from durable URL to channel without B7.6-style integration |

---

## 6. Proposed storage design direction

- **Storage class:** S3-compatible object store (or equivalent) when explicitly configured — consistent with comments in `supplier_offer_publish_safe_stub.py` (`EXPECTED_FUTURE_STORAGE`).
- **Contract:** Ingest pipeline produces **content-addressed or versioned object key**, optional **virus/transcode** steps later, and records **`public_url` or app-signed URL policy** in `publish_safe` when status leaves `deferred`.
- **Boundary:** Download from Telegram (`getFile`) only inside a dedicated ingestion service (future B7.4C scope as approved); **no** automatic publish on ingest.
- **Readiness:** Tighten review-package / operator_workflow only when product policy requires a durable asset (future B7.4E), to avoid blocking MVP prematurely.

---

## 7. Safest next implementation sequence

1. **B7.4B — Media storage ingestion contract / design doc**  
   API between “source reference” → “stored object” → “publish_safe fields”; failure modes; idempotency; no runtime code requirement in the doc itself.

2. **B7.4C — Minimal config + adapter/service + tests**  
   Plumb settings and a storage adapter behind an interface; unit tests with fakes/mocks; **no** auto-publish and **no** Telegram download wired until explicitly approved.

3. **B7.4D — Persist durable media metadata in `publish_safe`**  
   After successful ingest, write non-deferred metadata (`object_key`, `public_url` or policy pointer, `storage_kind`, timestamps) while preserving review authority.

4. **B7.4E — Review-package / readiness integration (if policy requires durable asset)**  
   Optional gate: block showcase publish until `publish_safe` is non-deferred **if** stakeholders require it — implement only with explicit policy sign-off.

5. **B7.5 — Rendered branded card asset**  
   Deterministic raster/vector card asset stored as its own object if product requires channel-grade creative separate from raw cover.

6. **B7.6 — Telegram `sendPhoto` / `sendMediaGroup` publish**  
   Prefer durable HTTPS (or stable Bot API file flow) over raw `file_id` where channel longevity matters; align with `telegram_showcase_client` behavior.

---

## 8. Test inventory to reference

Unit tests that regression-proof today’s media and showcase surfaces (run from repo root as usual):

- `tests/unit/test_supplier_offer_b7_1_media_review.py`
- `tests/unit/test_supplier_offer_b7_2_card_render_preview.py`
- `tests/unit/test_supplier_offer_cover_media_quality_review.py`
- `tests/unit/test_supplier_offer_review_package.py`
- `tests/unit/test_supplier_offer_b6_branded_preview.py`
- `tests/unit/test_supplier_offer_cover_photo_b3_1.py`
- `tests/unit/test_supplier_offer_showcase_ro.py`
- `tests/unit/test_operator_workflow_c2b8b_specs.py`
- `tests/unit/test_telegram_admin_moderation_y281.py`

(Additional supplier-offer tests may touch `showcase_photo_url` or moderation; the list above is the core **media / showcase / publish gate** set for future storage work.)

---

## 9. Explicit confirmations (B7.4A audit artifact)

This document and the B7.4A documentation step:

- **Did not** change application code.
- **Did not** add migrations.
- **Did not** touch the Mini App.
- **Did not** change booking, payment, or orders.
- **Did not** change publish readiness behavior in code.
- **Did not** perform real Telegram file download.
- **Did not** access production storage.

---

## References

- Saved handoff: [`docs/HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md`](HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md)
- Prompt that drove this audit: [`docs/CURSOR_PROMPT_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A.md`](CURSOR_PROMPT_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A.md)
