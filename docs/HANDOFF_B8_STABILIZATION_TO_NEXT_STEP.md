# Handoff: B8 stabilization → next step

Project: **Tours_BOT**

## Current checkpoint

**B8** recurring draft-tours slice is **implemented**, **stabilized**, and **reviewed** (see also [`HANDOFF_B10X_TO_B8_RECURRING_SUPPLIER_OFFERS.md`](HANDOFF_B10X_TO_B8_RECURRING_SUPPLIER_OFFERS.md), [`OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md) B8 slice 1).

### Behavior (unchanged in stabilization)

- **Endpoint:** `POST /admin/supplier-offers/{offer_id}/recurrence/draft-tours` (`count`, `interval_days`, `start_offset_days`).
- **Tour codes:** `B8R-*` for B8-generated rows; B10 primary bridged tours remain `B10-*`.
- **Generated tours:** `TourStatus.draft` — **not** `open_for_sale`; not Mini App–bookable until **`POST /admin/tours/{tour_id}/activate-for-catalog`** (B10.2) and any execution/routing policy you add per `Tour`.
- **No** Telegram channel publish, **no** orders/reservations/payments from B8.
- **B8** does **not** create or mutate `SupplierOfferTourBridge`; it only reuses **draft `Tour` insert mapping** from `SupplierOfferTourBridgeService` plus audit rows in `supplier_offer_recurrence_generated_tours`.

### Stabilization record

- **Docstring + docs + tests** only (no business-logic change in `supplier_offer_recurrence_service.py` behavior).
- **Tests:** `tests/unit/test_supplier_offer_recurrence_b8.py` (7 cases), `tests/unit/test_supplier_offer_tour_bridge_b10.py` (12) — all passing at stabilization.
- **Commit (example):** `dbd1272` — `test,docs: stabilize B8 recurring draft tours (guards, debt, idempotency notes)`.

## Architecture preserved

- `visibility` ≠ `bookability`
- Supplier offer = source facts; tour = customer-facing catalog object after controlled steps
- Mini App = execution truth; Layer A = booking/payment authority
- Admin = final decision maker; AI = draft packaging only (unchanged)
- No silent ORM, no AI-created tours, no supplier bypass of bridge rules (B-line)

## Tech debt (accepted for now)

- **Re-runs are not idempotent** — same body can create duplicate draft tours. Future: batch key or uniqueness on `(source_supplier_offer_id, departure_datetime)` (see `OPEN_QUESTIONS`).
- **`start_offset_days=0`:** first instance matches template `departure_datetime`; if B10 already bridged that date, B8 can still add another **draft** for the same window — use offset/ops discipline.
- **B7.3** media pipeline — still blocked on storage/download policy.
- **B10.6** bot router/consultant — still postponed.

## Next safe step options

1. **Product/ops —** define how each B8 **draft** `Tour` gets **Y27 execution link** (if needed) and **B10.2 activation** (manual per tour vs later explicit batch policy; **no** automatic catalog open without a ticket).
2. **Engineering —** optional **B8.2** idempotency / operator guardrails when admin UI volume justifies the design.
3. **Alternate —** **B7.3** when policy is ready, or **B11** when deep links are prioritized and catalog/activation story is stable.

**Do not** in the next slice without a new gate: automatic activation, silent recurrence jobs, or `SupplierOfferTourBridge` creation from B8.
