# B1 — Supplier offer intake + AI packaging + moderation (design) — completed

**Scope:** docs-only, accepted. **Detail:** [`SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md) **§§1–8**.

## Source of truth

- [`docs/SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md`](SUPPLIER_OFFER_INTAKE_AI_PACKAGING_MODERATION_DESIGN.md)
- [`docs/SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md`](SUPPLIER_OFFER_TO_TOUR_BUSINESS_PLAN.md)
- [`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)
- [`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md)

## Business principle

- Supplier provides **raw facts**.
- AI creates **draft packaging** only.
- Admin **reviews** / **edits** / **approves**.
- **Only** an **approved** package can be **published**.
- A **published** supplier offer should **later** **become** or **attach** to a **Tour** in the Mini App catalog **via an explicit bridge** (not silent ORM/AI).

## AI rules

- Draft only.
- No invented **dates** / **prices** / **seats**.
- No **publishing** by AI.
- No **booking** / **order** / **payment** side effects.
- No **silent** **Tour** creation.

**Also:** **Layer A** booking/payment **semantics** **unchanged**; **admin** **approval** **required** for customer-facing **authoritative** package (see design doc **§7**).

## Next safe step

**B2 — Supplier offer content/data upgrade** (schema, validation, persistence for B1 fields and status model without inventing `Tour` or breaking Layer A).
