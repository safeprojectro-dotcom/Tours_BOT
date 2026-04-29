# AI public copy — commercial fact lock contract

**Slice:** **1A** — source facts snapshot + fact-claim validator (read-side only).

**Related code:** [`app/services/supplier_offer_source_facts_snapshot.py`](../app/services/supplier_offer_source_facts_snapshot.py), [`app/services/supplier_offer_ai_public_copy_fact_lock.py`](../app/services/supplier_offer_ai_public_copy_fact_lock.py), review-package field **`ai_public_copy_review`** on **`GET /admin/supplier-offers/{offer_id}/review-package`**.

---

## 1. Principle

**AI is a copywriter and validator, not the source of commercial truth.**

Structured **`SupplierOffer`** (and, after bridge, **`Tour`**) fields remain authoritative for price, currency, dates/times, capacity, sales mode, discounts, payment mode, composition, and related facts. Any AI-generated or AI-polished text must be checked against a deterministic **source facts snapshot** before it can be treated as safe for downstream marketing use.

---

## 2. Source facts snapshot v1

**Purpose:** Stable, server-computed view of commercial fields for hashing and comparison.

| Aspect | Detail |
|--------|--------|
| **Version** | **`source_facts_version`:** **`v1`** |
| **Shape** | **`build_facts_dict_v1(offer)`** — normalized dict aligned with packaging grounding (title, description, program, included/excluded, departure/return ISO, boarding/transport/vehicle, **`base_price`**, **`currency`**, **`seats_total`**, **`sales_mode`**, **`payment_mode`**, **`service_composition`**, discounts, recurrence, hooks, marketing summary, cover reference). |
| **Hash / ref** | **`content_hash`** = SHA-256 over canonical JSON (**sorted keys**, UTF-8) of the facts dict (**`compute_facts_content_hash`**). |
| **Commercial facts** | Locked to ORM values at evaluation time; snapshot **does not** invent or edit DB state. |

Implementation entry point: **`build_source_facts_snapshot_v1(offer)`** → **`SourceFactsSnapshotV1`** (**`supplier_offer_id`**, **`content_hash`**, **`facts`**).

---

## 3. `packaging_draft_json.ai_public_copy_v1` expected shape

Persisted **optional** subtree for future AI workflows. **Slice 1A does not require** packaging generate to populate it automatically.

```json
{
  "snapshot_ref": "<hex sha256 of facts dict — must match live snapshot when present>",
  "fact_claims": {
    "base_price": "120.00",
    "currency": "EUR",
    "departure": "2026-09-01T08:00:00+00:00"
  }
}
```

| Field | Role |
|-------|------|
| **`snapshot_ref`** | Alias accepted: **`snapshot_content_hash`**, **`content_hash`**. Must equal live **`content_hash`** when set; otherwise **stale snapshot** (blocker). |
| **`fact_claims`** | Object whose keys must be a subset of **`ALLOWED_FACT_CLAIM_KEYS`** (same keys as **`build_facts_dict_v1`**). Unknown keys → blocker. |
| **`copy_slots`** *(future)* | Non-authoritative marketing-only slots (e.g. tone, CTA wording variants) — **not** validated as commercial facts in slice 1A; reserved for later slices. |

---

## 4. Fact lock behavior (`evaluate_ai_public_copy_fact_lock`)

| Result | Condition |
|--------|-----------|
| **Stale snapshot (blocker)** | **`snapshot_ref`** is non-empty and **≠** live **`content_hash`** (offer edited after AI draft). |
| **Unknown fact claim key (blocker)** | Key in **`fact_claims`** not in **`ALLOWED_FACT_CLAIM_KEYS`**. |
| **Fact mismatch (blocker)** | For each allowed key present in **`fact_claims`**, normalized value ≠ live snapshot (**decimals**, **ISO datetimes**, **ints**, stripped strings). |
| **Invalid `fact_claims` (blocker)** | **`fact_claims`** present but not a JSON object. |
| **Empty `fact_claims` (warning)** | **`ai_public_copy_v1`** present but **`fact_claims`** missing or empty — validator cannot assert commercial alignment. |

**Review-package integration:** **`AdminSupplierOfferAiPublicCopyReviewRead`** exposes **`fact_lock_passed`**, **`blocking_issues`**, **`warnings`**. Top-level review **`warnings`** include **`AI fact lock: …`** lines for blockers. **`recommended_next_actions`** may include **`resolve_ai_public_copy_fact_lock`** when the lock fails.

---

## 5. Current slice status (1A)

| Item | Status |
|------|--------|
| Source facts snapshot + hash | Implemented |
| Fact-claim validator | Implemented |
| **`review-package`** **`ai_public_copy_review`** | Implemented |
| External AI HTTP calls | **None** |
| Showcase HTML / **`build_showcase_publication`** | **Unchanged** |
| **`POST …/publish`** | **Unchanged** |
| Booking / payment / orders | **Unchanged** |
| Tour bridge / catalog activation | **Unchanged** |
| Packaging generate wiring **`ai_public_copy_v1`** | **Not required** for 1A; optional manual/test population of **`packaging_draft_json`** |

---

## 6. Future slices (non-binding roadmap)

1. Persist **`ai_public_copy_v1`** stub (e.g. **`snapshot_ref`** only) on **`POST …/packaging/generate`** when product asks for it.
2. AI copy generation (admin-triggered) writing **`fact_claims`** + optional **`copy_slots`** under validated prompts.
3. Explicit admin approval semantics for “approved marketing copy” distinct from packaging **`approved_for_publish`** if needed.
4. Use **approved** AI text **only** for **marketing slots**; **factual lines** in channel/Mini App remain driven by source-of-truth fields + deterministic formatters — see **[`ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md`](ADMIN_SHOWCASE_PUBLISH_RUNBOOK.md)** three-layer model.

---

## Document control

| Field | Value |
|-------|--------|
| **Created** | 2026-04-29 |
| **Kind** | Contract — AI fact lock slice **1A** |
