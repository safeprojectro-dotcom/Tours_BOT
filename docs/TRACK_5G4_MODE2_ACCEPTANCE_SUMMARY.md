# Track 5g.4 — Catalog Mode 2 (Mini App) — acceptance summary

**Status:** **closed** (Tracks **5g.4a–5g.4e**). This documents the **standalone catalog Mode 2** path on **Layer A** only — **not** Mode 3 (RFQ), **not** bridge execution, **not** a new payment stack.

**Reference prompts:** `docs/CURSOR_PROMPT_TRACK_5G4_MODE2_EXECUTABLE_SLICE.md` through `docs/CURSOR_PROMPT_TRACK_5G4E_ACCEPTANCE_AND_CLOSURE.md`.

---

## What was implemented (5g.4a–5g.4d)

| Slice | Scope |
|--------|--------|
| **5g.4a** | Whole-bus hold semantics gate: **`TemporaryReservationService`** only; charter catalog **`seats_count`** fixed to **`seats_total`** when policy allows; virgin rule enforced in policy/preparation. |
| **5g.4b** | After a valid Mode 2 virgin hold, same **`Order`** uses existing **`PaymentEntryService`** via **`POST /mini-app/orders/{id}/payment-entry`**; idempotent reuse unchanged. Tests lock the path. |
| **5g.4c** | Mini App **presentation only**: payment-forward CTA/copy (**Pay now**), assisted/partial full-bus wording **without** RFQ/custom-trip framing; multilingual where **`mini_app/ui_strings`** already branches (**en** / **ro** for touched keys). |
| **5g.4d** | **My bookings** / booking detail: human-readable **`facade_state`** labels; expired unpaid / closed-without-payment phrasing **without** raw enum triples; **`payment_session_hint`** humanized in read layer. |

**5g.4e** (this file): formal acceptance and closure — **no** production code requirement.

---

## User behavior now supported

- **Catalog → detail → preparation** for **`full_bus`** tours when **`mini_app_catalog_reservation_allowed`** (virgin inventory: **`seats_available == seats_total`**).
- **Whole-bus temporary reservation** with **`seats_count = seats_total`** only; partial inventory → **assisted/manual** catalog messaging, **not** RFQ fallback.
- **Reserve → reservation overview → Pay now →** existing **payment-entry** screen; timer and payment truth remain **backend-owned**.
- **My bookings** lists and booking detail show **Reserved temporarily**, **Payment pending**, **Reservation expired**, **Confirmed**, etc., via existing **`resolve_mini_app_booking_facade`** + localized shell labels — **not** raw **`booking_status` / `payment_status` / `cancellation_status`** combinations in the UI.

---

## Explicit non-goals (unchanged by 5g.4)

- **No** change to **`PaymentReconciliationService`**, reconciliation webhooks, or payment provider architecture.
- **No** change to **RFQ / bridge** execution, **5f v1** multi-quote contract, or **My Requests** hub logic beyond shared bookings APIs.
- **No** new **charter pricing model**, **supplier-defined** catalog Mode 2 execution policy, or **admin** booking mutations for this track.
- **Mode 1** per-seat catalog self-serve **unchanged** in meaning; shared Layer A services only.

---

## Postponed (explicit)

- Dedicated **charter / whole-bus pricing** model and **capacity** fields beyond current **`Tour`** pricing.
- **Supplier-defined** catalog Mode 2 policy path (execution still **`TourSalesModePolicyService`** / ORM tour).
- **Full localization** for every Mini App string (partial tables: **hu** / **it** / **de** may fall back to **en** for keys touched in **5g.4c–5g.4d**).
- **E2E / UI-runner** automation for Flet (unit/API tests cover behavior).
- **Private bot** charter product UX expansion (incidental read-side support is **not** expanded by **5g.4**).
- **RFQ bridge** CTA copy polish unless scheduled separately.

---

## Compatibility / must-not-break

- **Layer A** remains source of truth: **`TemporaryReservationService`**, **`PaymentEntryService`**, order/payment enums.
- Mini App stays a **thin** client over existing HTTP + services; **no** business rules duplicated in Flet for this track.
- Reopen **5g.4** only for **documented regressions** or **security** issues — **not** as a blanket new design track.

---

## Tests (existing coverage; no new suite required for 5g.4e)

Representative: **`test_api_mini_app`** (reservation, payment-entry, bookings list/detail labels), **`test_services_mini_app_booking_facade`**, **`test_track5g3_catalog_charter_copy`**, **`test_mini_app_booking_visibility_notes`**, **`test_mini_app_mode2_ux_polish`**, **`test_handoff_entry`** / charter assistance (unchanged semantics).

---

## Closure

The **catalog Mode 2 Mini App executable branch** (**5g.4a–5g.4e**) is **accepted and closed** unless a regression is filed.
