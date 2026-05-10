# HANDOFF_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT_TO_NEXT_STEP

## Checkpoint (B13G / B14A)

B13G full conversion smoke passed through exact Mini App tour routing:

- Offer **#12**, Tour **#6**, **`tour_code`** **`B10-SO12-04fb1f`**
- Execution link **#5** active
- **`conversion_status_panel`**: **`booking_link.active`**, **`customer_action.open_exact_mini_app_tour`**

**Remaining blocker (pre-B14C):** Mini App **`GET /mini-app/tours/{tour_code}/preparation`** → **`tour is not available for reservation preparation`**.

**B14A source trace:** **`MiniAppReservationPreparationService.get_preparation`** → **`PrivateReservationPreparationService.get_preparable_tour`** — for **`per_seat`**, **no** **`boarding_points`** ⇒ not preparable, while tour detail could still load.

---

## B14C status — **implemented**

**Purpose:** When the supplier-offer → tour bridge **creates a new** tour and the offer has usable **`boarding_places_text`**, materialize **`boarding_points`** so Layer A preparation can succeed (without weakening guards).

**Safety (observed for this change set):** no production API calls or data edits from implementation; no publish/retry/resend; no execution-link mutation; no orders/payments/reservations; no CTA change.

## Summary

**B14C** adds **`_materialize_boarding_points_for_new_tour`** on the **new-tour** bridge path. It fixes the **B14A** gap: **`per_seat`** tours need **`boarding_points`** for **`get_preparable_tour`**; the bridge previously copied offer copy/pricing but **not** stops.

## Changed files

| Path | Change |
|------|--------|
| `app/services/supplier_offer_tour_bridge_service.py` | **`_materialize_boarding_points_for_new_tour`**, **`BoardingPointRepository`**, **`parse_boarding_places`**; call after **`_ensure_default_translation`** in **`_insert_draft_tour_from_offer_dates`**; optional **`boarding_repo`** in constructor |
| `tests/unit/test_supplier_offer_tour_bridge_b10.py` | Five tests: materialize **\|**, idempotent replay, no text → no points, **Mini App prep** after **activate-for-catalog**, **link existing** unchanged |
| `docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md` | §6 / **§9** B14C note + code-path line |
| `docs/CHAT_HANDOFF.md` | **B14C** bullet |
| `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` | Tour **#6** / future bridge note vs **B14C** scope |
| `docs/HANDOFF_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT_TO_NEXT_STEP.md` | This file |

## What was fixed

- **New** tours from **`POST /admin/supplier-offers/{id}/tour-bridge`** (create path) and **`create_draft_tour_from_offer_dates`** / **`_insert_draft_tour_from_offer_dates`** get **`boarding_points`** when **`boarding_places_text`** parses to one or more non-empty lines (max **25**).
- **Idempotent:** if the tour already has boarding rows, **no** duplicates.
- **Layer A** guards unchanged; preparation still requires **`OPEN_FOR_SALE`**, seats, visibility, etc.

## What was not fixed

- **No** migration or script altering **existing** `tours` / **`boarding_points`** (e.g. production **Tour #6**).
- **`_link_existing`:** does **not** add boarding from the offer (existing tour data stays as-is).
- **Channel CTA** / showcase assembly **unchanged** (B14B still separate if needed).
- **Offers without** **`boarding_places_text`:** still produce tours **without** boarding → prep may still **404** for **`per_seat`** until ops adds stops.

## Tests run (all passed)

```text
pytest tests/unit/test_supplier_offer_tour_bridge_b10.py -q
pytest tests/unit/test_supplier_offer_catalog_conversion_closure.py tests/unit/test_supplier_offer_recurrence_b8.py tests/unit/test_services_mini_app_reservation_preparation.py -q
pytest tests/unit/test_supplier_offer_review_package.py -q
```

## Production note

- **No** production API calls or data edits were performed from this implementation work.
- **Deploy** does **not** automatically repair **Tour #6** (`B10-SO12-04fb1f`). After deploy, either **manually** add **`boarding_points`** for that tour in admin/DB (consistent with **`boarding_places_text`** on Offer **#12**) or accept a **B14D** ops prompt for a **safe** remediation checklist / smoke.

## Next recommended prompt

**`CURSOR_PROMPT_B14D_TOUR6_BOARDING_REMEDIATION_AND_MINI_APP_PREP_SMOKE`** — production **or** staging: verify/add **Tour #6** boarding rows **without** bridge replay side effects; then **`GET /mini-app/tours/B10-SO12-04fb1f/preparation`** smoke.

## Confirmations (this change set)

- **No** production API calls from the agent during implementation.
- **No** publish / retry / resend.
- **No** execution-link mutation.
- **No** orders, reservations, payments.
- **No** CTA / showcase URL behavior change.
- **No** weakening of **`get_preparable_tour`** / reservation guards.
- **No** data migration mutating existing rows.
