# HANDOFF_B8_3_DUPLICATE_ACTIVE_TOUR_ACTIVATION_GUARD

Project: Tours_BOT

## Status: implemented (B8.3)

Activation-time guard is **in** `AdminTourWriteService.activate_tour_for_catalog` (B10.2). There is **no** separate B8-only activation HTTP route.

**When it runs:** only if the tour is listed in `supplier_offer_recurrence_generated_tours` (B8-generated in audit sense).

**Conflict = block:** another `open_for_sale` tour with the **same** `departure_datetime` (DB equality) for the same template `source_supplier_offer_id`, and either:

- another row in `supplier_offer_recurrence_generated_tours` for that other tour, or
- the B10 **active** `supplier_offer_tour_bridges` row for that offer → that `tour_id` (primary bridged instance).

**Not blocked:** idempotent replay when the same tour is already `open_for_sale`. **Not blocked:** activation of a tour **not** in the B8 audit table (normal non-B8 activation unchanged).

**Error:** `AdminTourCatalogActivationStateError` → HTTP **400** with a clear message (no SQL/stack leakage).

**Code:** `app/services/admin_tour_write.py` · `app/repositories/tour.py` (`get_open_for_sale_conflict_for_recurrence_activation`) · `app/repositories/supplier_offer_recurrence_generated_tour.py` (`get_source_supplier_offer_id_for_tour`).

**Tests:** `tests/unit/test_supplier_offer_recurrence_b8.py` (sibling B8 + B10 bridge + idempotency + non-B8 + duplicate drafts allowed).

**Docs touch-ups:** `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, `docs/HANDOFF_B8_2_RECURRING_ACTIVATION_POLICY_TO_IMPLEMENTATION.md`.

### Future: legitimate second vehicle on the same date (open / ops policy)

B8.3 is intentionally strict for **MVP** to avoid accidental duplicate **catalog** rows for the same template offer and departure.

In operations, a supplier may run a **second vehicle** on the same route and calendar slot. **Preferred handling today (no new product):**

- **Same customer-facing product, more capacity:** increase `seats_total` (and coherently `seats_available`) on the **existing** active `Tour` rather than activating a second one.
- **Operationally distinct product:** a **separate** `SupplierOffer` and/or `Tour` so catalog and execution semantics stay unambiguous.

**Possible later enhancement (not in scope):** admin override to allow a second `open_for_sale` with explicit **reason**, **audit** trail, and **Mini App** copy rules. **Status:** open; see `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` (B8).

---

## Current checkpoint before B8.3 (historical)

B8 recurring draft Tour generation is implemented and stabilized.

B8.2 activation policy design is accepted.

Rules at that time:

- B8 creates recurring generated Tours as draft only.
- B8 does not auto-activate.
- B8 does not publish to Telegram.
- B8 does not create orders/reservations/payments.
- B8 does not create or mutate `SupplierOfferTourBridge` records.
- B10.2 remains the single activation path: draft Tour → `open_for_sale`.
- Mini App catalog uses backend truth and should only expose `open_for_sale` Tours.

Accepted B8.2 decision:

- duplicate draft Tours are accepted tech debt.
- duplicate `open_for_sale` Tours for the same supplier offer / same departure must be guarded at activation.
- guard lives in the existing activation path, not a separate B8-only endpoint.

## Goal of B8.3 (spec)

Activation-time guard: when activating a B8-generated Tour, block activation if another `open_for_sale` Tour already exists for the same source `SupplierOffer` and same `departure_datetime` (sibling B8 and B10-bridged primary in scope; see “Status” above).

Preserved: explicit admin activation; no auto-activation; no Telegram; no order/payment/reservation changes; no Mini App UI changes; no supplier-side or AI action.

## Expected result after B8.3 (acceptance)

- Duplicate B8 draft Tours may still exist.
- For **B8-audited** tours, only one `open_for_sale` per same source offer + same `departure_datetime` in the linked sense above.
- Idempotent activation replay for an already-`open_for_sale` tour still works.
- Normal non-B8 Tour activation still works.
- B10.2 / `POST /admin/tours/{tour_id}/activate-for-catalog` remains the only activation route.

## Known non-goals (unchanged)

- batch activation
- automatic recurrence scheduler
- generation idempotency
- B7.3 media pipeline
- B10.6 bot router redesign
- B11 deep links
- Y27 execution link automation
