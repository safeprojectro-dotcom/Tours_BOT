# B7.4B — Media storage ingestion contract and design

**Status:** design contract only (2026-05). **No runtime implementation** in this step.

This document defines how **durable media ingestion** should behave *before* code is written. It aligns with [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md) and existing B7.1 / B7.3B / C2B7.2a / C2B8A semantics.

---

## 1. Purpose and non-goals

**Purpose**

- Specify **when** ingestion may run, **what** sources are supported, **how** bytes flow from Telegram or URLs into app-owned storage, **how** storage is abstracted, **how** retries/idempotency work, and **how** `publish_safe` should transition from `deferred` toward a **durable** record—without weakening current publish and media gates.

**B7.4B is documentation only.** It does not ship behavior.

**Non-goals (explicit)**

- No application code changes.
- No database migrations.
- No object storage backend implementation or wiring to production buckets.
- No Telegram Bot API `getFile` or HTTP download execution in this step.
- No real storage reads/writes or credentials use for this document.
- No change to showcase publish behavior, handler UX, or readiness outcomes as implemented today.
- No Mini App work.
- No booking, payment, or orders.

---

## 2. Terminology

| Term | Definition |
|------|------------|
| **`source_media_reference`** | The **normalized string** the ingestion pipeline treats as the **authoritative source** for this attempt. For supplier offers, this should match the **approved** hero reference (see eligibility). May be `telegram_photo:{file_id}`, `https://…`, or (with policy) other supported schemes. |
| **`cover_media_reference`** | Column on `SupplierOffer`: supplier/intake reference to the current hero image. Ingestion must **not** treat this alone as approval; it must align with `media_review` (B7.1). |
| **`media_review`** | `packaging_draft_json["media_review"]` (B7.1): `status`, `cover_media_reference` **snapshot**, `reviewed_at`, `reviewed_by`, `reason`, etc. Authoritative for “may we treat this cover as approved for card.” |
| **`review_snapshot`** | `media_review.cover_media_reference` **at the time of human approval** (`approved_for_card`). Used to detect **drift** vs live `cover_media_reference`. |
| **`publish_safe`** | `packaging_draft_json["publish_safe"]` block. Today (B7.3B): metadata stub with `status: deferred`, no `object_key` / `public_url`. Future: holds **durable** metadata once ingestion succeeds. |
| **`durable_media_asset`** | Application-owned blob in object storage: stable **`object_key`**, known **`content_type`**, optional checksum/size, lifecycle owned by Tours_BOT—not ephemeral Telegram `file_id` and not a third-party URL alone. |
| **`object_key`** | Opaque storage key (e.g. S3 key) for the durable blob. Canonical identity for the asset inside our bucket/prefix. |
| **`public_url`** | Stable **HTTPS** URL suitable for Telegram `sendPhoto` **photo** argument *or* for downstream CDN use—when policy uses **public** objects; may be `null` if the design uses **signed URLs only** (then document `public_url` as absent and readiness uses a signer). |
| **`storage_kind`** | Enum-like string identifying backend/locator class, e.g. `none` (stub), `s3_compatible`, future `r2`, etc. Must not imply trust by itself; trust comes from auth + bucket policy. |
| **`ingestion_attempt`** | One logical run: **validate eligibility → resolve source → fetch bytes → validate → put object → update `publish_safe` (B7.4D)**. Has an idempotency key and audit trail (`attempt_id`, timestamps, errors). |
| **`publish_ready_asset`** | The asset the **product** requires before treating channel publish as “fully durable” (optional until B7.4E). At minimum: a **`durable_media_asset`** referenced from `publish_safe` with non-`deferred` status **if** policy requires it. Distinct from **`published`** (channel post already sent). |

---

## 3. Allowed source types

Future ingestion classifies `source_media_reference` (after normalization / trim):

| Pattern | Treatment |
|---------|-----------|
| **`telegram_photo:{file_id}`** | **Supported** for ingest **once** Bot API **`getFile`** + **HTTPS download of `file_path`** is implemented (B7.4C+). `file_id` must be non-empty after the prefix. No ingest without bot token and rate-limit strategy. |
| **`https://…`** | **Conditionally supported.** May be **fetched server-side** only when eligibility passes and policy allows **outbound HTTPS fetch** to that host. Treated as **copy into first-party storage**, not as “already durable”—URLs can rot, redirect, or serve different bytes later. TLS + size limits + timeouts required. |
| **`http://…`** | **Default: blocked** for durable ingest (cleartext, integrity, abuse). **Only** if an explicit **product/security policy** allows **time-bounded** fetch to known hosts (out of scope unless documented elsewhere). Prefer forcing HTTPS upload path instead. |
| **Empty / null** | **Never ingested.** No object created. |
| **Unknown / future schemes** (e.g. custom URI) | **Blocked** until added to this contract and to code. Return a strict **unsupported_source** class error. |

**Trust boundaries**

- **Telegram:** durable only **after** bytes land in our bucket; `file_id` remains non-durable until then.
- **HTTPS URL:** reference is **not** automatically first-party durable; ingestion **copies** into storage and records metadata in `publish_safe`.
- **HTTP:** unsafe default; align with security review before any exception list.

---

## 4. Ingestion eligibility gate

Ingestion is a **privileged** operation. It must run **only** when all **required** checks pass.

### 4.1 Required conditions (all must hold)

1. **`cover_media_reference`** on the row is **non-empty** (after trim).
2. **`media_review.status == approved_for_card`** (exact enum value used in B7.1). This **excludes** `replacement_requested`, `rejected_irrelevant`, `rejected_bad_quality`, and `fallback_card_required` without extra logic.
3. **No snapshot drift:** `review_snapshot` (`media_review.cover_media_reference`) **equals** current `cover_media_reference` (same rules as C2B8A / quality review).
4. **C2B7.2a alignment:** the same human-trust pattern as **OK photo / approve-for-card** — ingestion must not bypass “negative status on current hero” semantics documented for operators (see [`docs/HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md`](HANDOFF_ADMIN_COVER_REAPPROVAL_AFTER_REPLACEMENT_C2B7_2_DESIGN.md)). Requiring both **§4.1.2** and **§4.1.3** enforces that model.
5. **Source type** ∈ supported set (§3) for the configured build.
6. **Trigger** is explicit: admin/API action **or** an **opt-in** background worker flagged per deployment—**never** implied as a side effect of showcase publish unless a future slice explicitly designs that (default: **forbidden**).

### 4.2 Simplified eligibility table

| Condition | Ingestion |
|-----------|-----------|
| `approved_for_card` + aligned snapshot + supported source | **Allowed** (subject to §3 and ops flags) |
| `replacement_requested` / `rejected_*` / `fallback_card_required` | **Blocked** |
| Snapshot mismatch (`media_review_cover_snapshot_mismatch` semantics) | **Blocked** |
| Missing `cover_media_reference` | **Blocked** |
| Unsupported source type | **Blocked** |

### 4.3 Relationship to publish gates (today)

- **C2B8A** media blockers (`evaluate_cover_media_quality_review` / `cover_media_publish_blocking_reasons`) remain **separate**. Ingestion eligibility should **reuse the same notions** of drift and negative status so we **never** store bytes for covers that are not human-approved for the current hero.
- **Do not** weaken: operator_workflow, review-package, or “Preview before publish” workflows.

### 4.4 Publish must not auto-ingest (default)

- **`publish_showcase_channel`** (or any Telegram publish handler) **must not** silently call ingestion in MVP unless a **separate** approved design adds an explicit preflight with UX and idempotency. Default per B7.4A/B7.4B: **ingestion is orthogonal** to publish.

---

## 5. Storage adapter contract

Future code should depend on a **narrow adapter** so tests can fake storage without S3.

**Conceptual interface** (illustrative—names may vary in implementation):

```python
# Conceptual only — B7.4B does not add this to the codebase.

class StoredObject:
    object_key: str
    content_type: str
    byte_size: int
    etag: str | None
    metadata: dict[str, str]


class MediaStorageAdapter:
    def put_object(
        self,
        *,
        object_key: str,
        content_type: str,
        body: bytes,
        metadata: dict[str, str],
    ) -> StoredObject: ...

    def object_exists(self, *, object_key: str) -> bool: ...

    def public_url_for(self, *, object_key: str) -> str | None:
        """Return canonical HTTPS URL if bucket/object policy allows public read; else None."""

    def delete_object(self, *, object_key: str) -> None:
        """Optional: GC / rollback — use with care."""

    # If signed URLs are preferred over public_url:
    # def presigned_get_url(self, *, object_key: str, expires_in: int) -> str: ...
```

**Requirements**

- **`put_object`** MUST be atomic from the caller’s perspective (adapter handles retries).
- **Key naming:** predictable prefix per environment + **`supplier_offer_id`** + **content hash or version** (see §7) to avoid collisions.
- **Metadata:** store `source_media_reference` (truncated if needed), `offer_id`, `ingestion_attempt_id`, **no secrets**.
- **Security:** no world-writable buckets; **principle of least privilege** for runtime role.

---

## 6. Telegram `file_id`: getFile and download (B7.4C+)

**Not implemented in B7.4B.** Design expectations:

1. **Parse** `telegram_photo:{file_id}` → extract `file_id` string.
2. **Call** Bot API `getFile` with bot token → obtain `file_path`.
3. **Download** bytes via `https://api.telegram.org/file/bot<token>/<file_path>` (or documented Telegram file base). Apply **max byte size**, **MIME sniff bounds**, and **timeout**.
4. **Do not** persist bot token in `publish_safe` or logs.
5. **Handle** `file_id` expiry / 404: surface **`telegram_file_unavailable`**; do not partially update `publish_safe` to “ready.”

This pipeline is **only** invoked inside an ingestion service after eligibility (§4) succeeds.

---

## 7. Idempotency

**Problem:** double-clicks, retries, and worker redelivery must not create unbounded duplicate objects or flip-flop `publish_safe`.

**Recommended approach**

- **Idempotency key:** deterministic **`ingestion_id`** = hash of (`offer_id`, **normalized** `cover_media_reference`, **`review_snapshot`**, **`media_review.reviewed_at`** or monotonic `review_generation`). Alternatively store explicit **`media_review` version** field in future—until then use existing B7.1 fields.
- **Before put:** if `publish_safe` already documents **`status: ready`** (name TBD in B7.4D) **and** **`source_media_reference` matches** current eligible source **and** **`object_key` exists** (`object_exists`), **skip** re-download (return success).
- **On PUT conflict:** object key includes **content hash**; same bytes → same key → natural deduplication. Different bytes with same offer/version should not happen if eligibility ties to snapshot; if cover changes, **new** ingestion run with **new** key generation policy.
- **Failure:** record **`last_ingestion_error`** (or equivalent) in `publish_safe` **without** marking ready; do **not** delete existing durable object on transient failure.

Exact JSON field names for **`ready`** vs **`deferred`** vs **`failed`** are finalized in **B7.4D**; this contract requires **three conceptual states**: deferred (no durable asset), failed (last attempt error), ready (durable metadata present).

---

## 8. Evolution of `publish_safe` metadata

**Today (B7.3B stub)** — see `merge_publish_safe_into_draft` / `supplier_offer_publish_safe_stub.py`:

- `version`, `status: deferred`, `reason: no_durable_media_storage`, `storage_kind: none`, `object_key: null`, `public_url: null`, `source_media_reference`, `marked_at`, `marked_by`, `expected_future_storage`.

**After successful ingestion (B7.4D target—field sketch)**

- Bump **`version`** (e.g. `b7_4d`).
- **`status`:** `ready` (or `ingested`) — **not** `published`.
- **`storage_kind`:** e.g. `s3_compatible`.
- **`object_key`:** non-null.
- **`public_url`:** HTTPS **or** explicit omission if using **signed-URL-only** policy (document which).
- **`source_media_reference`:** echo of ingested source.
- **`ingested_at`**, **`ingested_by`** (actor or `system:worker`).
- **`content_type`**, **`byte_size`**, **`sha256`** (recommended for integrity and idempotency).
- **Remove or narrow** `reason: no_durable_media_storage` when leaving deferred.

**On cover change after ready**

- New cover → eligibility requires **new** `approved_for_card` with new snapshot → **new** ingestion supersedes old key policy (either **versioned keys** or mark `publish_safe` **stale** until re-ingest—B7.4D picks one; **never** silently keep old object as current hero).

---

## 9. Publish readiness and durable media (additive, no weakening)

**Today:** Readiness for showcase publish uses **review-package**, **operator_workflow**, and **C2B8A** media warnings. `publish_safe` being **deferred** does **not** block publish in current code.

**Future (optional B7.4E—policy gate):**

- Add **optional** readiness checks: e.g. “if publishing **with photo**, require `publish_safe.status == ready`” — **only** with product sign-off, so text-only modes are not accidentally blocked.
- Any new gate must **reuse** existing warning codes style or additive JSON flags so **dual-read** clients stay stable.
- **Never** remove or bypass C2B7.2a / negative-status / snapshot-drift protections in favor of “we have bytes.”

---

## 10. B7.4C — what to implement first

Recommended **first** slices (implementation order **within** B7.4C, still **no auto-publish**):

1. **Config surface** — environment variables or settings struct: storage backend toggle, bucket, prefix, region, max download bytes, feature flag **`ENABLE_MEDIA_INGESTION`** default **false**.
2. **`MediaStorageAdapter` fake** — in-memory or temp-dir fake implementing §5 for unit tests.
3. **`TelegramFileResolver`** interface — **stub** first: methods `get_file_info` / `download_bytes` **not** called from production paths until integration tests exist.
4. **Pure functions:** parse `telegram_photo:`, classify source type (§3), **eligibility predicate** mirroring §4 (unit-tested against fixtures from `tests/unit/test_supplier_offer_b7_1_media_review.py`, `test_supplier_offer_cover_media_quality_review.py`, `test_supplier_offer_review_package.py`).
5. **No** wiring to admin HTTP routes, **no** RQ/cron, **no** `publish_safe` write beyond existing stub until **B7.4D**.

---

## 11. Document inventory

| Document | Status |
|----------|--------|
| `docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md` | **Present** — primary upstream audit |
| `docs/CHAT_HANDOFF.md` | **Present** |
| `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` | **Present** |
| `docs/SUPPLIER_OFFER_PHOTO_MODERATION_CARD_GENERATION_DESIGN.md` | **Present** |
| `docs/ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md` | **Present** |
| `docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md` | **Present** |
| B7.1/B7.2/B7.3 handoffs / prompts in `docs/` | **Varies** — search `HANDOFF*B7*`, `CURSOR_PROMPT*B7*` as needed |

---

## 12. Alignment with existing identifiers (read-only reference)

- **`SupplierOfferMediaReviewService`** merges **`publish_safe` stub** whenever **`media_review`** is updated (`merge_publish_safe_into_draft`).
- **`COVER_MEDIA_PUBLISH_BLOCK_CODES_ALWAYS`** / **`evaluate_cover_media_quality_review`** encode drift and negative statuses used for C2B8A—ingestion eligibility should stay **consistent** with those semantics.
- **Stub constants** in `supplier_offer_publish_safe_stub.py`: `PUBLISH_SAFE_KEY`, `STATUS_DEFERRED`, `REASON_NO_DURABLE_STORAGE`, `STORAGE_KIND_NONE`, `EXPECTED_FUTURE_STORAGE`.

---

## References

- [`docs/B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md`](B7_4A_MEDIA_STORAGE_PIPELINE_READINESS_AUDIT.md)
- [`docs/HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md`](HANDOFF_MEDIA_STORAGE_PIPELINE_READINESS_B7_4A_TO_NEXT_STEP.md)
- Prompt: `docs/CURSOR_PROMPT_MEDIA_STORAGE_INGESTION_CONTRACT_B7_4B` (source instructions for B7.4B)
