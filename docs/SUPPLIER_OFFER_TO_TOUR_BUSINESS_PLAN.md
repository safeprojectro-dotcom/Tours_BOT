# Supplier offer → tour — BUSINESS plan (B1–B13)

**Phase:** Business / product planning **(documentation only)**. **No** code, **no** migrations, **no** runtime behavior in this file.

**Purpose:** Fix the **BUSINESS**-layer plan as the **authoritative sequence** for evolving supplier offers into **Mini App**-visible, **Layer A**-aligned **Tours**—without conflating this line with V2 **track numbers** (which record historical delivery) or with **Y** execution/messaging tickets.

**Aligns with (do not replace):**
- `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` — V2 Tracks **0–3** and marketplace expansion history.
- `docs/TECH_SPEC_TOURS_BOT_v1.1.md`, `docs/TECH_SPEC_TOURS_BOT.md` — product/technical baselines.
- `docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md` — Layer A must-not-break.
- Execution-link and conversion bridge work already documented (e.g. Y27, Y30, operator link workflow gates).

### Status (2026) — B10 → Mini App path

**B10** (supplier offer → **`Tour`** bridge) and **B10.1–B10.5** (draft/activate-for-catalog, **full_bus** Mini App conversion, package-priced **Layer A** holds, boarding fallback) are **implemented** and **smoke-accepted** (**Supplier offer #8 → Tour #4 → reservation / payment / My bookings**). **Mini App** remains **execution truth** for catalog booking. **Canonical** **handoff:** [`B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md).

---

## 1. Core business rule (non-negotiable)

**A published supplier offer must become or attach to a `Tour` in the Mini App catalog only through an explicit, auditable bridge**—**not** by silent ORM side effects, **not** by AI, **not** by supplier-only action.

- **“Become”** = create or bind a **Layer A** tour (or tour-shaped catalog row) per product policy.
- **“Attach”** = **execution / conversion link** (or successor contract) from **`supplier_offer` → `tour`**, with clear admin rules (see **B9** / **B10** and existing design gates).

This rule governs **B1–B13** and prevents accidental coupling of **moderation**, **AI packaging**, and **catalog truth**.

---

## 2. BUSINESS track overview (B1–B13)

| ID | Name | Intent |
|----|------|--------|
| **B1** | Supplier offer intake + AI packaging + moderation (design) | Raw supplier facts → draft AI packaging → admin approval before publication. **Design:** [`SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md). |
| **B2** | Supplier offer content / data upgrade | Schema + validation for intake fields, media references, program blocks, promos, recurrence hooks—**as needed** to implement B1. |
| **B3** | Supplier dialog upgrade | Telegram FSM/UX: step-by-step intake, one question at a time, validation—aligned with B1 dialog structure. |
| **B4** | AI packaging layer | Pluggable service contract: **draft-only** text/card outputs, **no** publish, **no** inventing commercial facts. |
| **B5** | Admin moderation & review | Surfaces to compare **raw** vs **AI draft**, edit/regenerate, approve/reject, clarification loops. |
| **B6** | Branded Telegram post template | Deterministic or templated public-channel presentation (brand, sections, CTA) once content is approved. |
| **B7** | Photo moderation & card generation | Safe media pipeline, optional card/preview image generation, moderation gates. |
| **B8** | Recurring supplier offers | Recurrence / series semantics for supplier routes (separate from one-off B1 intake; may require data model follow-on). |
| **B9** | Supplier offer → tour publication **bridge** (design) | Contract for **how** offer becomes/attaches to **Tour** and appears in Mini App; cites core rule §1. |
| **B10** | Supplier offer → tour bridge **implementation** | Runtime + migrations + admin flows to realize B9 without breaking Layer A. |
| **B11** | Telegram deep link routing | Stable `t.me/.../start` / callback routing for offer → Mini App / booking entry (aligned with product links). |
| **B12** | Admin/OPS visibility | Observability: offers, links, errors, operator surfaces (extends existing admin read patterns). |
| **B13** | Final smoke / production validation | End-to-end checklist: intake → moderation → publish → bridge → catalog → bookability smoke. |

---

## 3. Suggested sequence (not all gates are strict waterfalls)

- **B1** (design) → **B2** (data) → **B3** (dialog) can overlap in *planning*, but **implementation** should prefer: **B2** fields **before** heavy **B3**/**B4** wiring if persistence is incomplete.
- **B4** depends on B1 **output contract** and B2 **structured fields** (at least in principle).
- **B5** is the **control room** for human approval; it consumes B1 + B4 outputs.
- **B6**–**B7** can follow once **B5** can freeze “what gets published to Telegram and what assets exist.”
- **B8** is **logically** after a stable single-offer path (B1–B7), unless product explicitly sequences recurrence earlier.
- **B9** must be **accepted as design** before **B10** code; **B10** may reuse existing **execution link** / **conversion bridge** work—cite those docs in the ticket, do not fork concepts.
- **B11**–**B12** can proceed in parallel with B10 where safe.
- **B13** closes the slice for production.

---

## 4. Guardrails (whole BUSINESS line)

- **Layer A** booking, payment, reservation, reconciliation semantics remain **unchanged** unless a **separate** compatibility gate says otherwise (`TRACK_0` / Phase **7.1** alignment).
- **AI** (when introduced in B4/B1) is **draft-only**; it **must not** invent dates/prices/seats, **must not** publish, **must not** create **Tour**, **order**, or **payment** rows.
- **Supplier** cannot bypass **platform** moderation for public/market-facing publication (as in current Track **3** spirit).
- **RFQ** / **Layer C** and **supplier execution** (**Y** line) stay **separate product surfaces** unless a future gate explicitly integrates them.

---

## 5. Next safe step (BUSINESS)

- **Recommended (2026):** **B8 — Recurring supplier offers** — build on the **B10** bridge and stable **Tour** / **Layer A** path (see **B8** row in §2 table).
- **Alternate:** **B7.3 — Publish-safe media pipeline** when marketing surfaces need stored/downloaded assets per B7 design.
- **Completed / historical (do not re-scope as “next” without a new ticket):** **B2** data upgrade; **B6–B7.2** (see CHAT_HANDOFF BUSINESS line); **B9** bridge design; **B10** bridge implementation; **B10.1–B10.5** Mini App full_bus execution path — **[`docs/B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md)**.

---

## 6. Document control

| Document | Role |
|----------|------|
| This file | **BUSINESS** roadmap **B1–B13** + core bridge rule. |
| [`B10_X_SYNC_CHECKPOINT_2026.md`](B10_X_SYNC_CHECKPOINT_2026.md) | **B10.x** completion, smoke, gates, tech debt, **B8** / **B7.3** next-step pointer. |
| [`SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md) | **B1** detailed design. |
| `docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md` | Historical **V2** track delivery; use for **context**, not as a replacement numbering for **B** lines. |
