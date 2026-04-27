# HANDOFF_B8_2_RECURRING_ACTIVATION_POLICY_TO_IMPLEMENTATION

Project: Tours_BOT

## Current checkpoint

B8 recurring draft Tours are implemented and stabilized.

Current behavior:

- Admin can generate B8R-* draft Tour rows from an approved SupplierOffer.
- Generated Tours remain draft.
- Generated Tours are not open_for_sale.
- Generated Tours are not visible/bookable in Mini App catalog.
- No Telegram publish happens.
- No orders/reservations/payments are created.
- No SupplierOfferTourBridge records are created or mutated by B8.
- B8 uses supplier_offer_recurrence_generated_tours as audit/traceability.
- B8 may reuse shared draft Tour insertion mapping with B10 bridge service.
- Re-run behavior is currently non-idempotent and documented as accepted tech debt.
- start_offset_days=0 may duplicate the template/B10 bridged date and is documented as accepted tech debt.

Accepted stabilization commit:

- dbd1272 — test,docs: stabilize B8 recurring draft tours

## Architecture rules preserved

- visibility != bookability
- Supplier Offer is source facts
- Tour is customer-facing sellable catalog object
- Mini App is execution truth
- Layer A remains booking/payment authority
- Admin remains final decision maker
- AI remains draft generator only
- Recurrence generation does not mean activation
- Activation does not mean Telegram publish
- Publish does not mean booking/payment side effects

## B8.2 / B8.3 (accepted)

- **B8.2 (policy):** **explicit** **admin** **activation** **only;** **no** **auto**-**activation** **on** **generation.**
- **B8.3 (implementation):** **duplicate** **`open_for_sale`** **guard** **in** **`AdminTourWriteService.activate_tour_for_catalog`**: **tours** **listed** **in** **`supplier_offer_recurrence_generated_tours`** **cannot** **activate** **if** **another** **`open_for_sale`** **tour** **already** **exists** **for** **the** **same** **source** **supplier** **offer** **and** **same** **`departure_datetime`** **(sibling** **B8** **audit** **or** **B10** **active** **bridge** **tour).** **Idempotent** **replay** **unchanged.**

## Known risks

- Duplicate draft Tours are acceptable temporarily.
- Duplicate active Tours for the same source/date may confuse Mini App catalog and must be guarded.
- start_offset_days=0 can overlap with primary B10 bridge date.
- B7.3 media pipeline is still postponed.
- B10.6 Telegram bot router/consultant redesign is still postponed.
- B11 Telegram deep link routing is not in scope yet.

## Expected next implementation candidate

After the B8.2 Plan is accepted, the next implementation should likely be one small Agent step:

- either add activation guard for B8-generated Tours
- or add admin recurrence-generated visibility/read endpoint
- or document that existing activation path is sufficient

Do not implement automatic activation, Telegram publish, or booking/payment changes.