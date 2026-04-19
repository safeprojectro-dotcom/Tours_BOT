# CHECKPOINT_UVXWA1_SUMMARY

## Purpose
Compact continuity checkpoint after the accumulated completion of 5g/U/V/W/X/A1 and related hotfixes.

## Completed blocks (accepted)
- **Mode 2 / catalog whole-bus line:** Track **5g.4a**, **5g.4b**, **5g.4c**, **5g.4d**, **5g.4e**, **5g.5**, **5g.5b**.
- **Mode 3 customer:** **U1** (custom request UX), **U2** (lifecycle clarity), **U3** (My Requests IA).
- **Mode 3 ops/admin read-side:** **V1**, **V2**, **V3**, **V4**.
- **Mode 3 messaging:** **W1**, **W2**, **W3**.
- **Mode 3 supplier side:** **X1**, **X2**.
- **Admin UI:** **A1** operational surfaces (additive internal read-only UI).

## Live/prod fixes included in this checkpoint
- Supplier-offer `/start` payload/title hotfix.
- Request detail empty-control crash hotfix.
- Production schema drift fix for `custom_request_booking_bridges`.
- Custom request submit success-state hotfix.
- Custom request **422** validation visibility hotfix.

## Compatibility baseline (must remain unchanged)
- **Layer A** remains source of truth for booking/payment.
- **TemporaryReservationService** remains the only hold path.
- **PaymentEntryService** remains the only payment-start path.
- Service layer owns business rules; UI does not duplicate backend rule logic.
- **Mode 2 != Mode 3** (separate semantics).

## Postponed / non-goals (still postponed)
- Payment architecture redesign, reconciliation redesign, admin payment mutations beyond approved slices.
- RFQ/bridge execution semantics redesign.
- Broad supplier/admin/customer workflow redesign.
- Broad admin panel rewrite.

## Historical prompt classification
- Prompt files from **Track 0** through **Track 5g.5b** remain in repository as historical implementation/design trail.
- They are **not** all active tasks.
- They should **not** be mass-updated one-by-one by default.
- Active continuity source is: `docs/CHAT_HANDOFF.md` + `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` + current active prompt.

## Next recommended safe step
- **A2 (narrow):** admin custom-request operational usability pass (read-only/UI clarity only), using existing V1–V4/W3 truth without changing semantics.
