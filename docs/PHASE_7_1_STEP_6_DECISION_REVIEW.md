# Phase 7.1 / Sales Mode / Step 6 — Decision gate (direct whole-bus self-service)

**Status:** review complete — **no application code**, **no migrations**, **no refactors** in this checkpoint.  
**Date context:** aligns with `docs/CHAT_HANDOFF.md` continuity (Phase **7** `grp_followup_*` remains closed; Phase **7.1** Steps **1–5** shipped).

---

## 1. Current state summary

### What Phase 7.1 already implemented (Steps 1–5)

| Area | What exists |
|------|----------------|
| **Admin / source of truth** | `tour.sales_mode` (`per_seat` \| `full_bus`) on create/patch/list/detail; migration **`20260416_06`** on environments that follow deploy discipline. |
| **Backend policy** | `TourSalesModePolicyService` + `TourSalesModePolicyRead` — enum-driven; **no** inference from seat counts; shared interpretation for channels. |
| **Mini App** | Read-side reflects policy: `per_seat` keeps self-service prep/booking where allowed; `full_bus` hides misleading per-seat flow; assisted copy + **Request full-bus assistance** → support request with optional `tour_code` → structured handoff when policy requires operator path. |
| **Private bot** | Catalog/detail reflect policy; `full_bus` uses assistance CTA instead of prepare flow; forged self-service entry blocked; assistance callback **tour-scoped** → structured handoff **`reason`** when policy disallows self-service. |
| **Handoff / operator-assisted** | `handoffs.reason` carries compact **`full_bus_sales_assistance|…`** (tour, `sales_mode`, channel, optional hint). Admin DTOs expose **`is_full_bus_sales_assistance`**, **`full_bus_sales_assistance_label`**, **`assistance_context_tour_code`** so triage does not depend on `order_id`. |
| **Operations** | Prior **`tours.sales_mode`** schema drift on Railway was fixed by applying migrations — **process** lesson, not a Step 6 feature. |

### User-visible behavior today

**`per_seat`**

- Normal **self-service** journey: browse → prepare seats/boarding → temporary reservation → payment path (within existing MVP rules).
- Policy allows **`per_seat_self_service_allowed`**; Mini App and private bot expose the standard booking CTAs.

**`full_bus`**

- **No** whole-bus self-service reservation or payment in-app/bot.
- Clear **assisted** path: contact / assistance / support request with **structured** operator context (tour code, mode, channel).
- Operators can distinguish **full-bus commercial assistance** from generic support in admin handoff reads.
- Aligns with `docs/TOUR_SALES_MODE_DESIGN.md` §E: initial rollout **operator-assisted**; self-service seat selector must not be the primary commercial action for `full_bus`.

---

## 2. Gap analysis for direct whole-bus self-service

### Product / UX gaps

- **Price presentation:** Design calls for **`full_bus_price`** (fixed whole-bus commercial price), not `base_price × seats_count`. That field and admin UX are **not** implemented.
- **Purchase semantics:** “Buy whole bus” implies a single commercial line item, confirmation copy, and possibly different cancellation/deposit rules — **undefined** in current order/booking model.
- **Human gate:** Charter/full-bus deals often need **confirmation, contract, or allocation** before money — direct self-service skips that unless replaced by another explicit workflow.

### Operational / business gaps

- **Operator review** is **desirable by default** for many carriers: negotiated terms, invoicing, partial groups, school charters, etc.
- **Commercial risk** if customers pay before terms are agreed: refunds, chargebacks, seat-release semantics vs “whole unit sold” are not specified.

### Technical gaps (minimum before “safe” direct self-service)

From `docs/TOUR_SALES_MODE_DESIGN.md` and current codebase:

| Concept | Present? | Notes |
|---------|----------|--------|
| `sales_mode` | Yes | Step 1–2 |
| `full_bus_price` | **No** | Designed, not built |
| `bus_capacity` (optional) | **No** | Optional clarity vs `seats_total` |
| Dedicated **request / quote / approval** lifecycle | **No** | Would be new domain (states, timeouts, operator actions) — different from today’s `Order` + temporary reservation |
| **Payment semantics** for whole-bus | **No** | Current flow is seat-hold + pay; whole-bus may need deposit, invoice, or manual capture |
| **Operator approval state** | **No** | Not modeled; Phase 7 `group_followup_*` chain is **explicitly out of scope** for reuse as “full-bus approval engine” |
| Booking lifecycle **separation** for “commercial intent” vs “paid confirmed run” | **No** | Risk of overloading `TemporaryReservationService` / `reservation_creation` without a design pass |

**Conclusion:** direct whole-bus self-service would require **meaningful** schema and/or service design — not a thin UI toggle on top of the current per-seat engine.

### Risk if rushed now

- **Mis-priced or ambiguous checkout** (seat math vs whole-bus price).
- **Inventory semantics** (selling “one bus” vs decrementing `seats_available` in ways operators do not recognize).
- **Payment edge cases** (partial charter, changes, no-shows) without lifecycle support.
- **Coupling** to Phase 7 handoff machinery in ways that **reopen** closed scope.

---

## 3. Recommendation

**Choose one (selected):** **Stop at the current operator-assisted full-bus path for MVP/staging**, with **postpone direct whole-bus self-service to a later roadmap** until an **explicit product decision + design phase** (not Step 6 implementation).

This maps closest to outcome **1** (*assisted path sufficient for MVP/staging*), with outcome **2** (*needed later → design first*) as the **only** allowed path if the business later reverses the call.

**Do not** select outcome **3** (“needed soon, narrow slices”) **without** a written product mandate: technical prerequisites are too large for “soon” without design.

---

## 4. If direct whole-bus flow is recommended later — minimum safe rollout order

Only after a **design artifact** (update `docs/TOUR_SALES_MODE_DESIGN.md` + tech spec deltas + admin UX notes) is approved:

1. **Commercial model in data** — `full_bus_price` (and optional `bus_capacity` if product distinguishes commercial vs operational capacity); admin validation; migration plan.
2. **Dedicated request/approval (or quote) lifecycle** — new states or entity type; **do not** overload per-seat temporary reservation semantics until rules are written.
3. **Payment semantics** — deposit vs full pay vs manual off-PSP; reconciliation impact; idempotency.
4. **Customer UX** — Mini App + private bot flows **after** backend rules exist; still no “many seats ⇒ whole bus” heuristics.
5. **Final confirmation path** — operator confirms → customer pays or order becomes `confirmed` per chosen model; observability and admin reads.

Each step should be shippable with tests and deploy notes; **no** big-bang release.

---

## 5. If current assisted path is sufficient — explicit statement

**Yes — for MVP/staging, the current operator-assisted full-bus path is sufficient** given:

- The product already avoids misleading seat-based self-checkout for `full_bus`.
- Operators receive **structured** context (tour, mode, channel) without rediscovering basics.
- `docs/TOUR_SALES_MODE_DESIGN.md` already recommends **operator-assisted first**; implementation through Step **5** matches that stance.
- Direct self-service would not remove meaningful friction until **`full_bus_price`** and a clear lifecycle exist, and it would **increase** commercial and support risk if rushed.

**Friction:** assisted flow adds a human step — that is **acceptable** for charter-style sales in MVP/staging and matches “human confirmation” expectations.

---

## 6. Decision record (for handoff)

| Question | Answer |
|----------|--------|
| Proceed to **direct whole-bus self-service implementation** now? | **No** |
| Is Phase **7.1** “good enough” for MVP/staging? | **Yes** — Steps **1–5** deliver source of truth, policy, honest UX, and structured operator handoff for `full_bus` without pretending whole-bus ecommerce exists. |
| Minimum next step **if** product later demands direct self-service? | **Design-only** checkpoint: commercial fields + lifecycle + payment + admin + order model — **then** scoped implementation slices; **not** Step 6 code immediately. |

---

## 7. After completion — answers required by the gate

1. **Final recommendation:** **Stop at operator-assisted `full_bus` for MVP/staging**; **postpone** direct whole-bus self-service until explicit design + product approval.
2. **Step 6 implementation now?** **No** — Step **6** is satisfied as a **decision/review gate**; no implementation slice opened.
3. **“Good enough” for MVP/staging:** Phase **7.1** Steps **1–5** — `sales_mode` in admin, centralized policy, honest Mini App/private UX, structured full-bus assistance handoffs and admin triage labels; **no** `full_bus_price`, **no** direct whole-bus booking/payment.
4. **If yes later — minimum next design step before any code:** Single approved design addendum (pricing + lifecycle + payment + data model) under `docs/TOUR_SALES_MODE_DESIGN.md` / `docs/TECH_SPEC_TOURS_BOT.md` with explicit **out of scope** for Phase 7 `grp_followup_*` reuse and a **migration** plan when schema is touched.
