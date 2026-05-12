# B15B — Read-only Admin Publishing Console

**Status:** Implemented (read-only API).  
**Design context:** [`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`](B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md).  
**Code:** `app/api/routes/admin.py` · `app/services/admin_publishing_console_service.py` · `app/schemas/admin_publishing_console.py`.

---

## Endpoint

**`GET /admin/publishing-console`**

Same host/base URL as the rest of the Admin API (`/admin` prefix on the main API router).

---

## Authentication

Requires the **same admin gate** as other `/admin` routes:

- **`Authorization: Bearer <ADMIN_API_TOKEN>`**, or  
- **`X-Admin-Token: <ADMIN_API_TOKEN>`**

If `ADMIN_API_TOKEN` is unset in settings, the admin API returns **503** (admin disabled). Missing or invalid token → **401**.

---

## Query parameters

| Parameter | Type | Default | Constraints | Purpose |
|-----------|------|---------|-------------|---------|
| `limit` | integer | `20` | `1`–`50` | Max items returned after merge, sort, and filter. |
| `kind` | string | *(none)* | See below | Narrow **source** or filter by **console status**. |

### `kind` values

**Source narrowing** (only one family of cards):

- **`supplier_offer_initial`** — only supplier-offer channel candidates.
- **`tour_promotion`** — only open-catalog tour promotion candidates.

**Status filter** (both families fetched when `kind` is omitted, then filtered):

- **`ready`** — `console_status == ready`
- **`blocked`** — `console_status == blocked`
- **`needs_attention`** — `console_status == needs_attention`

Omitting `kind` returns a **merged** list: by default roughly half the budget for offers and half for tours (see implementation), sorted by status then kind/key, then truncated to `limit`.

Invalid `kind` → **422** (FastAPI validation).

---

## Response shape

Top-level model: **`AdminPublishingConsoleRead`**.

| Field | Description |
|--------|-------------|
| `items` | List of **`AdminPublishingConsoleItemRead`** (cards). |
| `total_returned` | Number of items in `items` (after `limit`). |
| `console_notice` | Fixed copy: read-only; no publish/send from this view. |
| `debug_notice` | Explains `offer_debug` / `tour_debug`. |
| `query_debug` | Echo of `limit`, raw `kind`, and normalized filters (support). |

### Item (`AdminPublishingConsoleItemRead`)

| Field | Description |
|--------|-------------|
| `candidate_key` | Stable id, e.g. `supplier_offer:12` or `tour:6`. |
| `kind` | `supplier_offer_initial` or `tour_promotion`. |
| `console_status` | `ready` \| `blocked` \| `needs_attention`. |
| `title` / `subtitle` | Human-facing labels. |
| `target_summary` | Short conversion/target line (offer id, optional `tour_code`, template hint; or conceptual exact-tour path for tours). |
| `next_best_action` | Suggested next step code/hint (from review-package or placeholder for tours). |
| `blocked_reasons` | Plain-language / technical blockers when applicable. |
| `human_summary` | One-line operator-oriented explanation. |
| `review_package_path` | e.g. `/admin/supplier-offers/{id}/review-package` (offers only). |
| `admin_tour_path` | e.g. `/admin/tours/{id}` (tours only). |
| `offer_debug` | Diagnostics for offers (`can_publish_now`, `next_missing_step`, template id, …). |
| `tour_debug` | Diagnostics for tours (code, seats, catalog visibility flag, …). |

---

## Candidate types and readiness assumptions

### `supplier_offer_initial`

- Built by calling existing **`SupplierOfferReviewPackageService.review_package`** per candidate offer (same aggregation as **`GET /admin/supplier-offers/{id}/review-package`**).
- **Offer pool:** recently updated offers (repository `list_for_admin`, capped scan batch in service).
- **Omitted from queue:** lifecycle **`published`** when **`conversion_closure.next_missing_step`** is **`null`** (conversion chain fully green — de-clutters console).
- **`console_status` (summary):**
  - **`blocked`:** lifecycle **rejected**, or AI **fact lock** blocking (`ai_block_present` and not `fact_lock_passed`).
  - **`ready`:** operator workflow exposes **`publish_showcase_channel`** with **`enabled: true`**.
  - **`needs_attention`:** otherwise (packaging, bridge, moderation, gates, etc.).

`can_publish_now` on the showcase preview remains **technical** readiness; the console **`ready`** flag for offers is aligned with the **publish** workflow action, not a second truth.

### `tour_promotion`

- Source: **`open_for_sale`** tours from **`TourRepository.list_by_departure_desc`** (batched read).
- **Catalog window:** **`tour_is_customer_catalog_visible`** (departure / `sales_deadline` vs “now”).
- **`console_status` (summary):**
  - **`blocked`:** not `open_for_sale`, departure in the past, or **`seats_available < 1`**.
  - **`needs_attention`:** not in customer catalog time window but otherwise saleable.
  - **`ready`:** open for sale, future departure, catalog-visible, at least one seat.

Tour cards are **promotion candidates** only; B15B does **not** create tour-specific channel drafts or templates (see B15D in design doc).

### Filters `ready` / `blocked` / `needs_attention`

When `kind` is one of these, the service still builds the appropriate source set(s), then **keeps only items** whose **`console_status`** matches. No extra semantics.

---

## Examples

```http
GET /admin/publishing-console
Authorization: Bearer <ADMIN_API_TOKEN>
```

```http
GET /admin/publishing-console?limit=10&kind=supplier_offer_initial
Authorization: Bearer <ADMIN_API_TOKEN>
```

```http
GET /admin/publishing-console?kind=tour_promotion&limit=15
Authorization: Bearer <ADMIN_API_TOKEN>
```

```http
GET /admin/publishing-console?kind=ready
Authorization: Bearer <ADMIN_API_TOKEN>
```

Example excerpt:

```json
{
  "items": [
    {
      "candidate_key": "supplier_offer:12",
      "kind": "supplier_offer_initial",
      "console_status": "ready",
      "title": "Excursie …",
      "target_summary": "supplier_offer #12 · tour_code B10-SO12-04fb1f · template …",
      "review_package_path": "/admin/supplier-offers/12/review-package",
      "offer_debug": { "supplier_offer_id": 12, "can_publish_now": true, ... }
    }
  ],
  "total_returned": 1,
  "console_notice": "Read-only publishing console preview. …",
  "debug_notice": "Technical fields are included …",
  "query_debug": { "limit": 20, "kind": null, ... }
}
```

*(Field values are illustrative.)*

---

## Read-only guarantees

This endpoint performs **SELECT-style ORM access** and **reuses read-only aggregations**. It does **not**:

- call Telegram or the channel adapter;
- insert or update publish-attempt rows;
- change supplier offer lifecycle, packaging, tours, orders, payments, or reservations.

---

## Explicit non-goals (B15B)

- **No** channel **publish**, **retry**, or **resend**.
- **No** **schedule**, **skip**, or **draft** persistence for the console.
- **No** **Telegram send** or side effects outside normal HTTP read DB access.
- **No** **execution-link** create/close/replace.
- **No** **order** / **payment** / **reservation** mutations.
- **No** change to **`GET /admin/publishing-console`** **semantics** (**read-only**). **B15C:** supplier-offer cards still derive from **`review-package`**; **exact-tour readiness** (execution link before publish, **`cta_rezerva_href`** → **`/tours/{code}`**) is reflected in that model — expect **`can_publish_now`** / **`publish_showcase_channel`** to stay **disabled** until the B15C chain is green. **Production smoke PASS (operator):** **[`docs/B15C_PRODUCTION_SMOKE_RESULT.md`](B15C_PRODUCTION_SMOKE_RESULT.md)**.

---

## Limitations (operational)

- **Cost:** supplier-offer cards trigger **one full review-package build per scanned offer** (bounded scan size). Large databases may want tighter limits or future caching (out of B15B scope).
- **Scope:** no RFQ / custom-request cards in B15B (optional placeholder was out unless safely supported).
- **Tour promos:** conceptual target line only; no dedicated promotion template or send path.

---

## Tests

- **`tests/unit/test_admin_publishing_console.py`** — auth, response shape, `kind=supplier_offer_initial`, `kind=tour_promotion`.

---

## Next step

**B15C** — implemented: **[`docs/B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md`](B15C_SUPPLIER_OFFER_EXACT_TOUR_CTA_GATE.md)**. **B15C6 (docs checkpoint):** **[`docs/B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md`](B15C_EXACT_CTA_CHAIN_CLOSURE_CHECKPOINT.md)** — stable baseline before the next console slice; **[`docs/HANDOFF_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT_TO_NEXT_STEP.md`](HANDOFF_B15C6_CLOSE_EXACT_CTA_CHAIN_CHECKPOINT_TO_NEXT_STEP.md)**. Forward: **B15D** (richer console read/admin surfaces, still no auto-publish/scheduler unless chartered) and **B15E–G** per **[`docs/B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md`](B15_ADMIN_PUBLISHING_CONSOLE_DESIGN.md)**.

**Related handoff:** [`docs/HANDOFF_B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE_TO_NEXT_STEP.md`](HANDOFF_B15B_READ_ONLY_ADMIN_PUBLISHING_CONSOLE_TO_NEXT_STEP.md).
