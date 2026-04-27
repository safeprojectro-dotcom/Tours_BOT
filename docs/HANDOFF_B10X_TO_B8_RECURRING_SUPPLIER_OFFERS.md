# Handoff: B10.x → B8 recurring supplier offers (slice 1)

**Status:** **B8 slice 1** implemented — explicit admin API to generate **additional** draft `Tour` rows from a packaging-approved **template** `SupplierOffer`, with audit rows. **No** `SupplierOfferTourBridge` on generated tours, **no** catalog activation, **no** booking/payment.

## Architecture (unchanged from B10.x)

- Bridge (B10) = one active `supplier_offer_tour_bridges` row per offer for the primary materialized tour when used.
- **Recurrence (B8 slice 1)** = **N** draft `tours` shifted by calendar days from the template offer’s departure/return span; tracked in `supplier_offer_recurrence_generated_tours` for audit.
- **Activation** = still **`POST /admin/tours/{id}/activate-for-catalog`** (B10.2) per tour.
- **Execution / customer booking** = existing Layer A + `supplier_offer_execution_links` (Y27) as product defines per instance (not in this slice).

## API

- **`POST /admin/supplier-offers/{offer_id}/recurrence/draft-tours`**
  - Body: `count` (1–24), `interval_days` (1–366), `start_offset_days` (0–730, default 0).
  - Eligibility: same as bridge materialization (packaging `approved_for_publish`, lifecycle not `rejected`, required fields on offer).
  - Response: `source_supplier_offer_id`, `items[]` with `tour_id`, `sequence_index`, `departure_datetime`, `return_datetime`.
  - Tour codes use prefix **`B8R`**; bridge-created tours still use **`B10-`**.

## Code

- `app/services/supplier_offer_tour_bridge_service.py` — shared `_insert_draft_tour_from_offer_dates`, public `create_draft_tour_from_offer_dates` (B8), `ensure_offer_eligible_for_tour_materialization`.
- `app/services/supplier_offer_recurrence_service.py` — `SupplierOfferRecurrenceService.generate_draft_tours`.
- `app/models/supplier_offer_recurrence_generated_tour.py` + migration `20260530_28`.
- Tests: `tests/unit/test_supplier_offer_recurrence_b8.py`.

## Stabilization notes (B8 slice 1)

- **B8 does not** create, update, or delete `supplier_offer_tour_bridges` — only `SupplierOfferTourBridgeService` mapping helpers for inserting **draft** `tours` rows.
- Generated tours are **`TourStatus.draft`**, not `open_for_sale`; no catalog activation in this path.
- **Re-run:** the same `POST` body may be issued twice; the second call creates **additional** draft tours (non-idempotent). See `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` (B8 tech debt).
- **start_offset_days=0:** first departure equals the offer’s `departure_datetime` (may **overlap** the primary bridged tour’s dates if the offer was already bridged to a `Tour` with the same — operators should use offsets or process discipline).

## Next (out of scope for slice 1)

- Linking each generated `Tour` to a supplier-facing execution path (execution links, separate offers, or series entity).
- Cron/worker or supplier-visible recurrence **without** admin POST (must stay explicit and policy-governed).
- B7.3 media pipeline when policy is ready.
