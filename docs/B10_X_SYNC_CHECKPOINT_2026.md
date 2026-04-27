# B10.x sync — supplier offer → Tour → Mini App (2026)

**Type:** documentation / handoff only. **No** `app/`, `mini_app/`, `tests/`, or `alembic/` changes in this checkpoint.

**Purpose:** Record **accepted truth** after **B9** design and **B10**–**B10.5** implementation + production smoke, align **`docs/CHAT_HANDOFF.md`**, **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`**, and related BUSINESS/bridge docs.

---

## 1) Completed (B9 → B10.5)

| Slice | Status | Notes |
|-------|--------|--------|
| **B9** | Design accepted | [`SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md) — explicit bridge, no silent Tour. |
| **B10** | Implemented | Admin bridge creates/links **Layer A** `Tour` from eligible offer; default **draft**; handoff: [`HANDOFF_B10_SUPPLIER_OFFER_TO_TOUR_BRIDGE_IMPLEMENTATION.md`](HANDOFF_B10_SUPPLIER_OFFER_TO_TOUR_BRIDGE_IMPLEMENTATION.md). |
| **B10.1** | Smoke | Tour created as **draft**; **not** visible in customer catalog until activated. |
| **B10.2** | Done | **Activate for catalog** gate before **`open_for_sale`** / customer visibility. |
| **B10.3** | Done | **Full_bus** fixed offer: **bookable as whole-vehicle package** in Mini App (not per-seat picker for that profile). |
| **B10.4** | Done | Fixed full_bus **reservation execution**: `total_amount` = **package** `tour.base_price` (not `base_price * seats_count`); `seats_count` = full charter capacity. |
| **B10.5** | Done | **Boarding fallback** for bookable fixed full_bus: server-resolved default boarding; optional `boarding_point_id`; no fake client id; prep state persisted across HTTP round-trips. |

**Design / prompt trail (non-exhaustive):** `docs/CURSOR_PROMPT_B10_SUPPLIER_OFFER_TO_TOUR_BRIDGE_IMPLEMENTATION.md`, B10.2 / B10.3 / B10.4 / B10.5 prompt docs, `docs/HANDOFF_B10_SUPPLIER_OFFER_TO_TOUR_BRIDGE_IMPLEMENTATION.md`.

---

## 2) Production smoke (accepted)

- **Path:** **Supplier offer #8** → **Tour #4** → **`open_for_sale`** → **full_bus** whole-vehicle **reservation** → **payment entry** → **My bookings** (temporary reservation visible).
- **Principle:** **Mini App** remains **execution truth** for catalog booking; the Telegram **channel post** and **“publish to Telegram”** are **separate** from **catalog** activation and **Mini App** bookability.

---

## 3) Safety gates (unchanged in meaning)

1. **Packaging / moderation:** e.g. **`approved_for_publish`** and related B5 rules **before** bridge eligibility.
2. **Bridge:** creates **`Tour`** as **`draft`** (or links per design) — **not** auto customer-catalog-open.
3. **Activation:** **explicit** **activate-for-catalog** / **`open_for_sale`** **before** listing in the Mini App catalog.
4. **Telegram public channel:** **publish to Telegram** is **separate** from **Mini App** catalog visibility and from **B10.2** activation.

These do **not** bypass: supplier review, admin approval, bridge, or activation — they document the **intended** chain.

---

## 4) Full_bus semantics (recorded)

- A **fixed ready-made** **`full_bus`** **catalog** tour is bookable as **whole bus / package**; **per-seat** **numeric** **choice** does **not** apply to that **fixed charter** profile.
- **Custom request / RFQ (Mode 3)** remains a **separate** product model (not conflated with this catalog full_bus path).
- **Package price:** order **total** for **`FULL_BUS`** self-serve holds = **`tour.base_price`** (whole-vehicle), not per-seat × seats.
- **Per_seat** catalog tours: **unchanged** (per-seat pricing and boarding selection rules).

---

## 5) Postponed tech debt

- **B10.6 — Telegram bot tour detail:** should become **router / consultant** (e.g. deep links to **Mini App**), **not** a **second catalog** with duplicated “sold out” / debug / stale copy. **Do not** fix in the B10.x doc-only window; track in [`OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md).
- **Secrets:** if **`ADMIN_API_TOKEN`** (or other secrets) appeared in **logs** or **chat** during smoke, **rotate** in deployment after smoke.

---

## 6) Next safe step (product)

| Option | ID | Note |
|--------|-----|------|
| **Recommended** | **B8** | **Recurring supplier offers** on top of the bridge — see [`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) B8 row. |
| **Alternate** | **B7.3** | **Publish-safe media pipeline** (see B7 design docs). |

---

## 7) Document control

| File | Role |
|------|------|
| This file | B10.x **sync checkpoint** (completed path + smoke + gates + debt + next). |
| [`CHAT_HANDOFF.md`](CHAT_HANDOFF.md) | **Points** to this checkpoint (short summary at top). |
| [`OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) | **B10.6** and cross-links. |
| [`SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md) | B-line roadmap; **B10** done; **next** B8 / B7.3. |
| [`SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md`](SUPPLIER_OFFER_TO_TOUR_BRIDGE_DESIGN.md) | B9 design + **B10** implementation status note (**§10** = status + forward pointer, 2026-04-27). |
