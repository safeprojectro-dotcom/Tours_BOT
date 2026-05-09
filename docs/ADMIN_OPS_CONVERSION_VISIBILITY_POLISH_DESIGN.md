# Admin/OPS conversion visibility polish (design only)

**Project:** Tours_BOT. **Proposed slice id:** **`C2B11A_ADMIN_OPS_CONVERSION_STATUS_PANEL`**.

**Type:** Design for a **read-only** status panel — **no** mutations, **no** Mini App, **no** booking/payment/order changes in scope.

**Related:** [`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`](CONVERSION_CHAIN_OPS_SMOKE_READINESS.md) · **GET** `/admin/supplier-offers/{id}/review-package` (schema: [`app/schemas/supplier_admin.py`](../app/schemas/supplier_admin.py)) · [`docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`](B10_6_BOT_AS_ROUTER_DESIGN_GATE.md).

---

## Purpose

Operators and admins **confuse** layers:

- **Showcase published** vs **Tour bridged** vs **catalog listed** vs **execution link** vs **customer bookable**.

That confusion drives wrong **support** answers, **premature** publish, and false “it’s live” messaging. This design proposes a **single read-only panel** (HTTP **review-package** projection + compact **Telegram admin card** mirror) using **five stable labels** and **plain-language** statuses — **mapped from existing** read models, **not** new business rules.

---

## Current problem

- **`review-package`** already contains the data (`offer.lifecycle_status`, `linked_tour_catalog`, `execution_links_review`, `conversion_closure`, `showcase_preview`, `operator_workflow`), but it is **spread across** sections and **mixed** with **warnings**, **AI**, and **media** quality.
- Operators **shortcut** to “**published**” or “**active**” and **collapse** **catalog** vs **booking link** vs **Layer A** bookability.
- **Telegram** card shows **operator_workflow** text but **not** a **fixed grid** of the five layers.

---

## Proposed read-only status panel

**Where (future implementation):**

1. **HTTP:** A dedicated subsection in **`AdminSupplierOfferReviewPackageRead`** **presentation** (or a named block in **OpenAPI/docs**) — e.g. **`conversion_status_panel`** — derived **only** from existing fields (computed **read-only** DTO **or** documented **view** of current JSON).
2. **Telegram:** Compact **five-row** (or **five-line**) block on the **private admin offer** detail, **refreshed** with **`review_package_refresh`**, **no** new callbacks required for the panel itself.

**Rules:**

- **Read-only** — panel **never** triggers POSTs.
- **Deterministic** mapping from **`review-package`** — **no** duplicate readiness logic in the **bot**; **reuse** the same service output as HTTP.
- **Hide** internal enums from default panel; use **recommended labels** below.

---

## Recommended labels (five layers)

| Layer | What it answers |
|--------|-----------------|
| **Showcase** | Is the **marketing / channel** side published for this offer? |
| **Tour bridge** | Is there a **materialized `Tour`** linked to this offer (bridge)? |
| **Catalog** | Is that **Tour** **listed for sale** in the **Mini App** catalog sense? |
| **Booking link** | Is the **supplier offer → Tour** **execution link** active for deep routing? |
| **Customer action** | What can the **customer** do **right now** (honest, Layer A–aware)? |

---

## Status examples (operator-facing wording)

These are **display** suggestions — implementation maps from **`review-package`** booleans and known blockers.

### Showcase

| Status | Meaning |
|--------|---------|
| **Published** | Lifecycle / showcase path indicates **published** to channel (per existing rules). |
| **Not published** | Not yet **published** (draft/approved path — use existing lifecycle). |
| **Blocked** | **Cannot** publish yet (packaging/moderation/showcase preview/**configured** blockers — point to **`operator_workflow`**, **`warnings`**, **`showcase_preview`**). |

### Tour bridge

| Status | Meaning |
|--------|---------|
| **Linked** | **`has_tour_bridge`** / **`active_tour_bridge`** present. |
| **Missing** | No bridge / no linked tour row for this offer. |

### Catalog

| Status | Meaning |
|--------|---------|
| **Listed for sale** | **`linked_tour_catalog`** indicates catalog listing / **`open_for_sale`** (aligned with **`catalog_listed_for_mini_app`** / tour status). |
| **Not listed** | Bridge may exist but **not** listed for sale. |
| **Blocked** | **Cannot** activate (missing fields, **`b8_same_offer_date_conflict`**, policy guard, etc.). |

### Booking link

| Status | Meaning |
|--------|---------|
| **Active** | **`execution_links_review.active_link`** present and applicable. |
| **Missing** | **No** active link (or not **published** — align with **`can_create_execution_link`** / precheck note). |
| **Stale** | **Optional** UX bucket: link exists but **suspected** mismatch (e.g. **replaced** tour, **superseded** link — **product** defines trigger; **initial** slice may **collapse** Missing/Active only). |

### Customer action

| Status | Meaning |
|--------|---------|
| **Open exact Mini App Tour** | **`conversion_closure`** / B11 readiness: customer can open **exact** tour for booking **subject to** Mini App rules. |
| **Not bookable yet** | Honest **intermediate** state (published only, catalog only, or no link — **not** “bookable”). |
| **Assisted fallback** | **full_bus**, **past** departure, **blocked**, or **contact operator** path — **no** false **“book now”**. |

---

## What **not** to show (default operator panel)

- **Raw enum leakage** — internal DB/API enums as primary text.
- **Generic “Active”** without **layer** — forbidden; always **scoped** (Showcase / Catalog / Booking link).
- **“Bookable”** **unless** **Layer A** can **actually** execute the **booking path** for that tour state — prefer **“Open in app”** / **Mini App will show availability”** if semantics are **delegated** to the app.

Internal **`operator_workflow.actions[].code`** stays in **advanced** / **developer** tooling or **logs**, not the **default** five-row panel.

---

## Recommended implementation slice: `C2B11A_ADMIN_OPS_CONVERSION_STATUS_PANEL`

**Scope (future PR — not in this doc step):**

- Add **read-only** **`conversion_status_panel`** (name TBD) to **`review-package`** response **or** document **strict** rendering from existing fields.
- Render the **same** panel (compact) on **Telegram** admin offer detail.
- **No** new POST routes, **no** **operator_workflow** mutation changes, **no** **Mini App**, **no** **booking/payment/order** changes.

**Tests:** Snapshot or serializer tests that **given** a frozen **`review-package`**, **panel** rows match **expected** labels (table-driven from `test_supplier_offer_catalog_conversion_closure`-style fixtures).

---

## References

- Operator playbook: [`docs/ADMIN_OPERATOR_WORKFLOW.md`](ADMIN_OPERATOR_WORKFLOW.md)
- Ops smoke: [`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`](CONVERSION_CHAIN_OPS_SMOKE_READINESS.md)
- Customer copy alignment: [`docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`](B10_6_BOT_AS_ROUTER_DESIGN_GATE.md)
