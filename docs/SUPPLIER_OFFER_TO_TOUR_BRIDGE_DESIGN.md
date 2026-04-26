# Supplier offer → Tour bridge (B9 design)

**Status:** design only (B9). **No** migrations, **no** `app/` code, **no** automatic Tour creation in this document.

**Aligns with:** [`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) §1 (explicit bridge, no silent ORM, no AI Tour); existing **Y27.1** `supplier_offer_execution_links` (operator **link to existing** tour) — B9/B10 add the **create-from-offer** path and the **governance** contract for when a Tour is allowed to exist in the catalog.

**Prerequisite work ( implemented in repo, not repeated here ):** B1–B4.3 intake/packaging/truth, **B5** packaging review, **B6** branded preview, **B7.1** media review metadata, **B7.2** `card_render_preview` plan. None of these create a `Tour` row for the Mini App catalog by themselves.

---

## 1. Core principle

| Concept | Role |
|---------|------|
| **Supplier offer** | Source of **commercial and operational** facts: raw/proposed product, **not** the Layer A sellable contract until bridged. |
| **Tour** | **Layer A** **customer-facing** catalog and booking object (`tours` + translations + policy). |
| **Bridge** | An **explicit, admin-controlled** action (API / admin UI) that **creates** a new `Tour`, **or** **binds** the offer to an **existing** `Tour`, per rules below. **Not** a DB trigger, **not** supplier-only, **not** AI. |

**Invariant:** A supplier offer does **not** “silently” become catalog-visible. Publication to Telegram, packaging approval, and **bridge to Tour** are **separate** concerns (B5 `approved_for_publish` ≠ automatic catalog Tour).

---

## 2. Preconditions (gate before any bridge)

### 2.1 Packaging and moderation

- **`packaging_status` = `approved_for_publish`** (B5). Draft or rejected packaging must not pass the bridge gate without a new approval/repair path defined in B10.
- **Quality / warnings:** `quality_warnings_json` and `missing_fields_json` should be **empty of blocking codes** for the product’s B10 allow-list, **or** admin has explicitly **acknowledged** residual warnings (B10 may persist `bridge_warnings_acknowledged` or equivalent). **B9** does not prescribe SQL — only the rule: **no “unknown gaps” in price, dates, or capacity** for the target Tour.

### 2.2 Supplier offer lifecycle (exact safe MVP policy)

**Recommended gate for B10 MVP:**

- Allow bridge when `lifecycle_status` is one of:
  - **`approved`** (central moderation passed), **or**
  - **`ready_for_moderation`** **only if** product explicitly extends B10 to allow “bridge before publication” (default **reject**; prefer **`approved` or `published`** per business).

**Stricter default (safest for catalog integrity):** require **`approved`** **or** **`published`**, and **packaging** **`approved_for_publish`**. Tighten or loosen in B10 with explicit product sign-off.

**Disallow bridge when:** `rejected`, `draft` (unless a separate “admin draft tour” product exists — out of B9 scope).

### 2.3 Required field completeness (for the mapped Tour)

Align with existing `Tour` and `SupplierOffer` models:

| Area | Expectation |
|------|-------------|
| **Title** | `supplier_offers.title` non-empty. |
| **Description / program** | Map from `description`, `program_text`, `marketing_summary` (order TBD in B10);** no** empty program if catalog policy requires it. |
| **Departure / return** | `departure_datetime`, `return_datetime` present; `duration_days` on Tour = derived calendar span (≥1). **Recurrence** (B8) out of B9 scope — one-off only unless B10 adds rules. |
| **Price** | `base_price` + `currency` (non-null for sellable; if bridge creates **draft** Tour, B10 may allow null only if `Tour` schema and catalog rules allow—today `tours.base_price` is **NOT NULL** — bridge must supply values or block). |
| **Capacity / mode** | `seats_total` valid; `sales_mode` set (`per_seat` / `full_bus`). `vehicle_label` / boarding: map as available; boarding points may be **post-bridge** admin edit if not in offer. |
| **Included / excluded** | Map to `tour_translations` fields when creating default language row. |

### 2.4 Media (optional, non-blocking for MVP)

- `cover_media_reference` and B7.1 `media_review` can be **incomplete** for **draft** Tour creation if product chooses; **public** marketing surfaces may require B7.3+ before `open_for_sale`. **B9** does not require S3 or `getFile` in the bridge.

---

## 3. Bridge output: create vs link

| Option | When |
|--------|------|
| **A — Create new Tour** | **Recommended MVP** when no suitable catalog Tour exists. Admin (or B10) runs **“create tour from offer”** → insert `tours` + default `tour_translations` + set `seats_available` per policy, then **link**. |
| **B — Link to existing Tour** | Reuse for **merging** into an already-managed departure (same product rules, **same** `sales_mode`, compatible dates). **Operator flow** already uses manual tour pick + `supplier_offer_execution_links` (Y27). B10 should **not** fork that table’s meaning; **link** = new or updated row in `supplier_offer_execution_links` with `tour_id` of **existing** tour. |

**MVP sequence (recommended):** **(1)** create `Tour` in **`draft`** (see §6), **(2)** insert **active** `SupplierOfferExecutionLink` (`supplier_offer_id`, `tour_id`, `link_status='active'`), **(3)** optional second admin step sets Tour to **`open_for_sale`** when catalog policy allows.

**Idempotency (§7):** If an **active** link already exists for the offer, **return** the existing `tour_id` and **do not** create a second Tour (unless “replace” flow closes the old link per Y27 rules).

---

## 4. Data mapping (offer → `Tour` + translations)

| `supplier_offers` | `tours` / `tour_translations` |
|-------------------|-------------------------------|
| `title` | `tours.title_default` and default row `tour_translations.title` (e.g. `ro` or `en` per product default). |
| `description` / `marketing_summary` | `short_description_default` / `full_description_default` and matching translation fields; B10 chooses split (e.g. first paragraph short). |
| `program_text` | `tour_translations.program_text`. |
| `included_text` / `excluded_text` | `included_text` / `excluded_text` on default translation. |
| `departure_datetime` / `return_datetime` | `tours.departure_datetime` / `return_datetime`; `duration_days` = `max(1, (return_date - departure_date).days)` in calendar days or product rule. |
| `base_price` / `currency` | `tours.base_price` / `currency`. |
| `seats_total` | `tours.seats_total`; **`seats_available`** = `seats_total` at creation for `per_seat` **or** `0` / `seats_total` for `full_bus` per §5 and Layer A policy. |
| `sales_mode` | `tours.sales_mode` (same enum family). |
| `cover_media_reference` | `tours.cover_media_reference` (optional, nullable). |

**Code:** `tours.code` must be **unique** — generate deterministic admin-prefixed or sequential code in B10; **not** the supplier’s free-text reference alone if collision-prone.

---

## 5. Full bus vs per seat

- **`per_seat`:** `seats_total` / `seats_available` follow normal catalog rules; Mini App self-serve only where `TourSalesModePolicyService` allows (existing Phase 7.1 behavior).
- **`full_bus`:** Create Tour with `sales_mode = full_bus`. **Do not** present standard per-seat checkout as “full bus for one seat” — catalog actionability should remain **`assisted_only` / `view_only`** as today for full bus when not bookable. **Payment / assisted closure** follows existing `SupplierOfferPaymentMode` + Layer A; bridge **must not** flip policies silently.
- **Accidental per-seat booking for a full_bus Tour:** Blocked by existing sales-mode and catalog policy, not redefined in B9 — B10 only ensures **`tours.sales_mode`** is **not** set to `per_seat` for a `full_bus` offer.

---

## 6. Status mapping (new Tour and catalog visibility)

- **`tours.status`:** `TourStatus` includes `draft`, `open_for_sale`, …
- **Safest MVP:** New Tour from bridge starts as **`draft`**. It **does not** appear as a normal **open** catalog item until an admin (or a **separate** explicit action) sets **`open_for_sale`** and any Layer A gating.
- **Alternative (product option):** Single-step **bridge + open for sale** only if **all** B7 media + pricing gates are green — document in B10; default remains **draft first**.

**Supplier offer** `lifecycle_status` / `published_at` are **not** automatically updated by the bridge in B9 design; if product wants `published` only after Tour is live, that is a **B10** policy flag.

---

## 7. Idempotency and single active link

- **Idempotent `POST`:** Same admin request with same idempotency key (B10) returns the **same** `tour_id` and link id when an **active** `supplier_offer_execution_link` already exists for `supplier_offer_id`.
- **One active link** per offer at a time (matches Y27). **Replace** = close previous link with `replaced` / operator workflow, then create new.
- **No duplicate Tours** for the same offer and same idempotency window — server returns **200** with existing resources.

---

## 8. Audit (minimum fields for B10)

Record (dedicated table **or** extended metadata on the link row — B10 choice):

- `supplier_offer_id`, `tour_id`
- `bridge_status` (e.g. `created` | `linked` | `failed` | `superseded`)
- `initiated_by_user_id` / **admin** actor (existing `X-Admin-Actor-Telegram-Id` → `users.id` pattern)
- `created_at`, `completed_at` (if async)
- **Snapshot** reference: `packaging_draft_json` hash or version string, `packaging_status`, optional **frozen** JSON blob for legal traceability
- `reason` / `notes` (free text for “why this tour”)
- If **not** reusing `supplier_offer_execution_links` for audit only, a **`supplier_offer_tour_bridge`** table can store **create** events separately from **execution** links; avoid two conflicting truths — **one** active link to **one** tour is canonical for booking.

**Existing** `SupplierOfferExecutionLink` already ties offer ↔ tour for execution; B10 “create from offer” should **create Tour + one active link** in one transaction where possible.

---

## 9. Non-goals (B9 and typical B10 slice)

- **No** automatic Telegram **channel** publish of the offer or the Tour.
- **No** payment, order, or booking mutation in the bridge handler itself.
- **No** Mini App **UI redesign**; catalog visibility follows existing Tour status + APIs.
- **No** **recurrence / series** generation (B8) in this design.
- **No** **media download**, **S3 upload**, or **getFile** in the bridge.
- **No** **AI** rewriting of `supplier_offers` or `tours` **source of truth** — mapping is **mechanical** from approved fields.
- **No** supplier-self-service bridge — **admin** (or future **central** role only) in MVP.

---

## 10. Next implementation: B10

**B10** (separate tickets) should include:

1. **Migration** as needed: optional **`supplier_offer_tour_bridge`** audit table **or** columns on `supplier_offer_execution_links` / `supplier_offers` (e.g. `bridged_tour_id`) — **one** model of truth for “which tour this offer is selling.”
2. **Admin API:** e.g. `POST /admin/supplier-offers/{id}/tour-bridge` with body `{ "mode": "create" | "link", "tour_id": ... }` and idempotency header.
3. **Read** bridge status on admin offer detail.
4. **Tests** + **smoke** (e.g. offer **#8** with `approved_for_publish` → Tour **draft** or **open** per policy → catalog visibility matches `Tour.status` and existing Mini App filters).

**Smoke expectation:** Tour appears in Mini App **catalog** only when **`tours.status`** and catalog query rules allow (e.g. `open_for_sale` + not cancelled), not merely because a bridge row exists.

---

## Document history

- **2026-04-26:** B9 design — initial version (no code).
