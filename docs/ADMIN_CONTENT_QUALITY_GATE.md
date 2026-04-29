# Admin Content Quality Gate — Slice 1

**Scope:** Read-only admin visibility on **`GET /admin/supplier-offers/{offer_id}/review-package`**. **Does not** change booking/payment, showcase publish, Mini App UI, Tour bridge, catalog activation, or execution links.

**Implementation:** [`app/services/supplier_offer_content_quality_review.py`](../app/services/supplier_offer_content_quality_review.py) (**`evaluate_content_quality_review`**), schema **`AdminSupplierOfferContentQualityReviewRead`**, aggregated into review-package **`warnings`** and **`recommended_next_actions`**.

---

## 1. Purpose

Production smoke showed that a supplier offer can be **technically valid** (packaging approved, bridge, **`open_for_sale`**, catalog-visible) while still carrying **weak / placeholder / inconsistent marketing content** (e.g. discount code without value, thin hooks, short descriptions).

Operators need **deterministic warnings** before publish, catalog emphasis, or AI-assisted public-copy work—not silent reliance on supplier drafts alone.

---

## 2. Current Slice 1 behavior

| Aspect | Behavior |
|--------|----------|
| **Where** | Response field **`content_quality_review`** on **`GET …/review-package`** (**`warnings[]`** with **`code`** / **`message`**, **`has_quality_warnings`**). |
| **Blocking** | **None.** APIs and workflows behave as before. |
| **Top-level `warnings`** | Each item is also prefixed into the merged list as **`Content quality [{code}]: {message}`**. |
| **`recommended_next_actions`** | May include **`review_supplier_offer_content_quality`** when **`has_quality_warnings`** is **true** (guidance only). |

---

## 3. What it checks (deterministic)

**From packaging helpers** ([`assess_missing_and_warnings`](../app/services/supplier_offer_packaging_service.py), [`assess_packaging_truth_warnings`](../app/services/supplier_offer_packaging_service.py)):

- Missing or weak **`base_price`** / **`currency`**, empty **`program_text`**, invalid **`seats_total`**, undefined included/excluded, etc. (codes such as **`missing_price`**, **`weak_program`**, **`inclusions_undefined`**).
- **`orphan_promo_code`**: **`discount_code`** set without **`discount_percent`** or **`discount_amount`** &gt; 0.
- **`discount_deadline_without_value`**: **`discount_valid_until`** without an actual percent/amount discount.
- **`scarcity_language_unsubstantiated`**: urgency/scarcity wording in title/description without live inventory truth in this pipeline.

**Additional Slice 1 heuristics** (same module):

- **`short_hook_very_short`**: non-empty **`short_hook`** shorter than 20 characters.
- **`short_hook_equals_title`**: **`short_hook`** matches **`title`** (case-insensitive).
- **`marketing_summary_thin`**: non-empty **`marketing_summary`** shorter than 120 characters.
- **`description_thin`**: non-empty **`description`** shorter than 80 characters.

Codes are de-duplicated by **`code`** per response.

---

## 4. What it does not do

- **Does not** block **`POST …/publish`**, **`POST …/tour-bridge`**, **`POST …/activate-for-catalog`**, or execution-link endpoints.
- **Does not** auto-edit supplier rows or run migrations.
- **Does not** call external AI or change deterministic showcase HTML (**[`supplier_offer_showcase_message`](../app/services/supplier_offer_showcase_message.py)**).
- **Does not** alter Layer A booking/payment paths.

---

## 5. Relation to AI Fact Lock (Slice 1A)

| Mechanism | Focus |
|-----------|--------|
| **[`AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md`](AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md)** | Protects **commercial facts** against drift when optional **`ai_public_copy_v1.fact_claims`** exists (snapshot hash, mismatches). |
| **Content Quality Gate (this doc)** | Surfaces **weak or inconsistent source/marketing copy** before publish-like decisions. |

Both are **admin-review safeguards** on **`review-package`**; neither replaces **`approved_for_publish`** or moderation lifecycle gates.

---

## 6. Future slices (non-binding)

1. Stronger **optional** pre-publish gate (product decision—still no silent automation).
2. **Admin UX** surfacing **`review-package`** fields without collapsing separation of gates.
3. **AI copy generation** under **[fact-lock contract](AI_PUBLIC_COPY_FACT_LOCK_CONTRACT.md)**.
4. Dedicated **content cleanup / edit** workflow for operators.

---

## Document control

| Field | Value |
|-------|--------|
| **Created** | 2026-04-29 |
| **Kind** | Admin Content Quality Gate — **Slice 1** (docs) |
