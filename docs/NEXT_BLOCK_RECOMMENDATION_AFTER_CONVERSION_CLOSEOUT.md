# Next block recommendation — after conversion closeout

**Project:** Tours_BOT. **Context:** Telegram conversion chain (**C2B8B**, **C2B10T-A/B/C**, **C2B10T-D**) and **media foundation** pause (**B7.4A–D**) documented in [`docs/TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md`](TELEGRAM_CONVERSION_AND_MEDIA_FOUNDATION_CHECKPOINT.md).

**This doc:** Explicit **priority order** for **next implementation** — complements [`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`](CONVERSION_CHAIN_OPS_SMOKE_READINESS.md) §8 (options table).

---

## Option comparison

| Option | Label | What it is | Main risk if done too early |
|--------|--------|------------|-----------------------------|
| **A** | **Production/OPS smoke** | Human **Mode A/B** walkthrough + **`review-package`** checks on real env — [`docs/PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md`](PRODUCTION_E2E_SUPPLIER_OFFER_WALKTHROUGH.md). | Ops **misread** states during smoke → **wrong** conclusions without a **status panel**. |
| **B** | **B10.6 Bot-as-router** | Private bot **router/consultant** copy + CTAs — [`docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`](B10_6_BOT_AS_ROUTER_DESIGN_GATE.md). | **Customer** messaging **diverges** from **operator** vocabulary; duplicate/stale “catalog” in chat. |
| **C** | **Admin/OPS visibility panel** | Read-only **five-layer** panel — **`C2B11A`** in [`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`](ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md). | None critical — **read-only**, **bounded** slice. |
| **D** | **Resume media pipeline** | **B7.4D2**, ingestion, **B7.4E**, **B7.5**, **B7.6** per charter. | **High** cost; **lower** immediate **booking** value vs conversion clarity; **needs** explicit **charter** (checkpoint says **paused**). |

---

## Recommended order (explicit)

1. **`C2B11A_ADMIN_OPS_CONVERSION_STATUS_PANEL`** — Admin/OPS **read-only** conversion status panel (**Option C**).
2. **Production/OPS smoke** — **Option A** (walkthrough + live **`OFFER_ID`** validation **after** panel exists).
3. **B10.6 Bot-as-router** — **Option B** (customer routing + copy **after** **ops** and **smoke** share **one** vocabulary).
4. **Media pipeline** — **Option D** **only** after **explicit** product/security **decision** (not automatic continuation from **B7.4D**).

---

## Why this order

1. **Status panel first** — **Read-only**, **no** booking/payment/Mini App risk; **reduces operator mistakes** and **`published` vs `bookable`** confusion **before** more human smoke or customer-facing bot work.
2. **Production smoke second** — Safer when **checklist** and **panel** **agree**; smoke logs become **auditable** against **Showcase / Bridge / Catalog / Booking link / Customer action**.
3. **B10.6 third** — Bot-as-router **benefits** from **confirmed** **labels** and **training** on the **panel**; avoids shipping **customer** explanations **before** **internal** alignment (see B10.6 recommendation).
4. **Media pipeline last** — **Lower immediate business value** for **conversion closure** than **ops clarity** and **routing**; already **paused** at **B7.4D** until **charter**; bytes/storage introduce **infra** and **policy** load.

---

## Completed closeout docs (reference)

- [`docs/CONVERSION_CHAIN_OPS_SMOKE_READINESS.md`](CONVERSION_CHAIN_OPS_SMOKE_READINESS.md)
- [`docs/B10_6_BOT_AS_ROUTER_DESIGN_GATE.md`](B10_6_BOT_AS_ROUTER_DESIGN_GATE.md)
- [`docs/ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md`](ADMIN_OPS_CONVERSION_VISIBILITY_POLISH_DESIGN.md)
- This file: [`docs/NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md`](NEXT_BLOCK_RECOMMENDATION_AFTER_CONVERSION_CLOSEOUT.md)

**Handoff:** [`docs/HANDOFF_CONVERSION_CLOSEOUT_AND_NEXT_BLOCK_GATE_TO_NEXT_STEP.md`](HANDOFF_CONVERSION_CLOSEOUT_AND_NEXT_BLOCK_GATE_TO_NEXT_STEP.md)
