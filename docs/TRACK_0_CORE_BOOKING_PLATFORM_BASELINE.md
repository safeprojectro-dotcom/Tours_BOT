# Track 0 — Core Booking Platform Baseline (Frozen Core)

**Status:** baseline for all **V2 supplier marketplace** tracks (`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`).  
**Scope:** documentation + compatibility contracts + smoke/guardrails only — **no** new product features in Track 0.

---

## 1. Purpose

Before **Track 2+** (supplier admin, publication, request marketplace), the project must treat the existing implementation as **Layer A — Core Booking Platform**. This document freezes that core: what it is, what must not break, and what to verify before/after each future track.

**Related design (extension, not part of frozen core behavior):**

- `docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`

**Original MVP spec (historical baseline):** `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`.

---

## 2. Frozen Core — What Is In Scope (Layer A)

The following are **stable, shipped behaviors** that supplier-marketplace work must **preserve** unless a future track explicitly scopes a breaking change with migration and rollout plan.

### 2.1 Tours and catalog

- **Central admin** is source of truth for tours (create/patch, boarding, translations, archive) per existing admin API.
- **Catalog read paths** used by Mini App and private bot must continue to load tours consistently with ORM/schema (including fields required by current code, e.g. `sales_mode` after Phase 7.1).
- **`seats_total` / `seats_available`:** operational inventory; reservation hold decrements `seats_available`; expiry/cancel paths restore per existing rules (see Phase 5/6 notes, `OPEN_QUESTIONS` §18 for conservative `seats_total` patch semantics).

### 2.2 Per-seat booking flow

- **Prepare → temporary reservation (hold)** for **`sales_mode=per_seat`** (and any path where self-service seat selection remains allowed) must keep:
  - idempotent/safe hold creation where already implemented
  - `seats_count` > 0 and within availability rules
  - order row lifecycle: `reserved` + `awaiting_payment` + active cancellation + `reservation_expires_at` semantics
- **No implicit switch** of commercial semantics via UI-only logic; policy remains service-owned (`TourSalesModePolicyService` for sales-mode **interpretation**).

### 2.3 Temporary reservation lifecycle

- Hold window rules (relative to departure and `sales_deadline` cap) remain as implemented.
- **Lazy expiry** / worker behavior: unpaid hold expires → seats restored (capped at `seats_total`), payment/cancellation fields updated per existing implementation — must not regress.

### 2.4 Payment entry and reconciliation baseline

- **Payment session** creation/reuse and **webhook/API reconciliation** remain the **single** authority for transitioning to paid where implemented.
- **Idempotency:** later non-paid events must not regress a paid order.
- **No duplicate reconciliation** logic in bot or Mini App UI.

### 2.5 Mini App — current stable behavior

- **Routes and flows** accepted under Phase 5 MVP (catalog, tour detail, preparation, hold, payment entry, mock completion when enabled, bookings list) must remain functional for **`per_seat`** tours.
- **Read-side `sales_mode`:** Mini App reflects `TourSalesModePolicyRead` (e.g. seat selector vs full-bus messaging) — must not invent parallel rules in the client.

### 2.6 Private bot — current stable behavior

- **Language**, catalog browsing, tour deep links, preparation/hold where implemented.
- **Phase 7** group CTAs: `grp_private` / `grp_followup` payloads, narrow handoff persistence for `grp_followup` only — unchanged.
- **Read-side `sales_mode`:** bot copy/CTAs follow policy service — unchanged contract.

### 2.7 `sales_mode` support (Phase 7.1)

- **`tour.sales_mode`** enum: `per_seat`, `full_bus` — persisted on `tours`; admin read/write as shipped.
- **`TourSalesModePolicyService`:** single service-layer interpretation; driven by enum, not by inferring mode from `seats_*` alone.

### 2.8 Assisted full-bus path (Phase 7.1 Step 5)

- **No direct whole-bus self-service reservation/checkout** as the default frozen behavior.
- **Structured operator-assisted path:** handoff reason / context for full-bus sales assistance (e.g. `full_bus_sales_assistance` family), admin read-side flags/labels as shipped — must remain coherent with existing admin handoff mutations (Phase 7 narrow `group_followup_*` semantics unchanged).

### 2.9 Handoff baseline (Phase 7, closed)

- **Narrow** `group_followup_start` chain: assign-operator, mark-in-work, resolve-group-followup, queue labels — **do not** broaden or reopen as part of supplier marketplace tracks without explicit scope.

### 2.10 Production / migration guardrail (learned incidents)

**Schema drift is a deploy-class incident**, not “random API bugs”:

1. **`tours.cover_media_reference`** — code deployed before Alembic `20260405_04` applied → `UndefinedColumn` on tour-loading routes (`CHAT_HANDOFF` operational note).
2. **`tours.sales_mode`** — code deployed before Alembic `20260416_06` applied → `column tours.sales_mode does not exist` → bot/Mini App/admin any path loading `Tour` fails (`COMMIT_PUSH_DEPLOY.md`, `OPEN_QUESTIONS` §17/§20).

**Rule:** for any environment, **`alembic current` must match `alembic heads`** (or the intended revision set) **before** or **with** deploy of code that expects new columns/enums; then **smoke** tour-loading and `/health`.

---

## 3. Compatibility Contracts (Future Tracks Must Preserve)

### 3.1 Per-seat booking semantics

- Hold creation, seat decrement, expiry restore, and order status fields for the existing self-service path must remain correct for `per_seat` tours.
- Changing pricing or seat math for `per_seat` requires an explicit scoped track + tests + migration safety.

### 3.2 Payment semantics

- Reconciliation remains the single paid-state transition authority.
- No new payment “side doors” from supplier UI without reconciliation alignment.

### 3.3 Reservation timer semantics

- TTL calculation and `sales_deadline` interaction unchanged unless explicitly redesigned.
- Workers/job timing assumptions stay valid.

### 3.4 Mini App routes and expectations

- Existing public/mini-app endpoints used by the Flet client keep backward-compatible behavior for current clients unless versioned intentionally.
- New fields may be **additive**; breaking removals require explicit client + API coordination.

### 3.5 Private bot routes / CTAs

- `/start` payloads (`tour_*`, `grp_private`, `grp_followup`) and catalog flow must not break.
- Handoff persistence rules for `grp_followup` unchanged.

### 3.6 Admin baseline (already implemented)

- Admin tour/order/handoff surfaces as shipped (Phase 6 + Phase 7 + Phase 7.1 read-side flags) remain valid.
- New supplier admin must **not** replace or silently bypass central admin invariants without explicit design.

---

## 4. Must-Not-Break Checklist (Compact)

Use this **before and after** each V2 track merge/deploy.

### 4.1 Booking core

- [ ] `per_seat` hold creates order + decrements `seats_available` correctly
- [ ] Expiry restores seats (capped by `seats_total`)
- [ ] Waitlist eligibility still matches “sold out” semantics where applicable
- [ ] `TourSalesModePolicyService` still centralizes sales-mode interpretation

### 4.2 Payment core

- [ ] Payment entry + webhook path still idempotent
- [ ] Paid order cannot be regressed by late non-paid events

### 4.3 Mini App

- [ ] Catalog and tour detail load (no 500 from ORM/schema)
- [ ] `per_seat` booking path still works end-to-end in staging
- [ ] Full-bus tours do not expose a **fake** self-service seat checkout if policy says assisted-only

### 4.4 Private bot

- [ ] Catalog / tour browse / prepare path works for `per_seat`
- [ ] `grp_private` / `grp_followup` payloads unchanged in behavior
- [ ] Full-bus copy matches policy (assisted CTA, not seat-by-seat pretense)

### 4.5 Handoff baseline

- [ ] `group_followup_start` narrow admin mutations unchanged in meaning
- [ ] Phase 7.1 full-bus assistance handoff still visible to admin reads as today

### 4.6 Migrations / deploy

- [ ] `python -m alembic current` vs `alembic heads` aligned on target DB
- [ ] No deploy of code expecting new DDL before migration apply
- [ ] `/health` and `/healthz` OK post-deploy
- [ ] Smoke at least one route that **loads `Tour`** (e.g. mini-app catalog or admin tour list)

---

## 5. Baseline Smoke Checks (Minimum)

Run **locally and/or staging** (and production after prod deploy) as appropriate.

### 5.1 Always

| Check | Expect |
|--------|--------|
| `GET /health` | 200 |
| `GET /healthz` | 200 |
| `alembic current` (on target DB) | matches deployed code expectations / `heads` |

### 5.2 Tour / schema sanity

| Check | Expect |
|--------|--------|
| Mini App catalog (or `GET` mini-app tour list equivalent) | 200, no `UndefinedColumn` |
| Admin `GET /admin/tours` (with token) | 200 |
| Load one tour with `sales_mode` visible | `per_seat` or `full_bus` as configured |

### 5.3 Booking / payment (staging)

| Check | Expect |
|--------|--------|
| `per_seat` prepare → hold → payment entry (mock if enabled) | same behavior as pre-track |
| Hold expiry (optional shorter TTL in staging) | seats restored |

### 5.4 Bot / Telegram (staging)

| Check | Expect |
|--------|--------|
| Private `/start` + open catalog | works |
| `grp_followup` still creates narrow handoff when applicable | unchanged |

---

## 6. Track 0 Exit Signal

Track 0 is **complete** when:

1. This document exists and is referenced from `docs/CHAT_HANDOFF.md` and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`.
2. `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` Track 0 points here as the compatibility baseline.
3. Team agrees that **all V2 tracks** will run **§4 + §5** before/after merges that touch Layer A or shared ORM/schema.

**Next V2 track after Track 0:** **Track 1 — Supplier Marketplace Design Package** (documentation acceptance / alignment against this baseline — **no** application code).

**After Track 1 acceptance:** **Track 2 — Supplier Admin Foundation** is the next **implementation** track; it must preserve **§3–§5** (compatibility contracts + smoke) for any Layer A or shared schema work. See **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`**.

---

## 7. Explicit Non-Goals (Track 0)

- No supplier entity, supplier admin, channel publication, or request marketplace implementation.
- No new DB tables for marketplace in Track 0.
- No broad refactor of booking/payment/bot/Mini App.
