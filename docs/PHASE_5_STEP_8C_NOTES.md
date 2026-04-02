# Phase 5 Step 8C — staging data hygiene (TEST_BELGRADE_001)

## Purpose

Keep the **TEST_BELGRADE_001** smoke path reproducible: after repeated manual tests, staging DB accumulates orders/payments and the tour can reach **sold out** (`seats_available = 0`) or **stale calendar** (departure/sales in the past). That blocks **prepare** and is **data state**, not a Mini App UI defect.

## Scripts

| Script | Role |
|--------|------|
| `scripts/staging_belgrade_helpers.py` | Shared: delete order-related rows for a tour, rolling `departure` / `return` / `sales_deadline`, stdout **SMOKE_READY** checks. |
| `scripts/reset_test_belgrade_tour_state.py` | **Light reset:** removes booking artifacts for `TEST_BELGRADE_001`, restores seats/status, **refreshes dates**, prints validation. |
| `scripts/seed_test_belgrade_tour.py` | **Full re-seed:** same deletes as reset for existing tour, replaces boarding + translations path, **rolling dates** on every run. |

## Why prepare was “unavailable”

The Mini App calls `GET .../preparation`; the API returns **404** when the tour is not preparable (`app/services` / `PrivateReservationPreparationService.get_preparable_tour`): typically **no seats**, wrong **status**, **no boarding points**, or missing localized tour assembly. **Stale sales_deadline** (in the past) breaks **confirm** later because reservation expiry cannot be computed — keep dates in the future via reset/seed.

## Operational loop

1. Before a **full** catalog → prepare → booking → payment smoke, run **reset** (or **seed** if the tour is missing or you need a clean rebuild).
2. Read stdout: last line **`SMOKE_READY=YES`**.
3. Run the smoke; expect **one** new reservation for the dev Telegram user.
4. Repeat **reset** before the next long regression if seats were consumed again.

**PowerShell (repo root, `DATABASE_URL` set):**

```powershell
python scripts/reset_test_belgrade_tour_state.py
```

## My bookings vs DB

My bookings lists only orders for the **synced Telegram user** (`MINI_APP_DEV_TELEGRAM_USER_ID` on staging), not every row in `orders`. See `docs/PHASE_5_STEP_8B_NOTES.md`.

## Out of scope

Booking rules, webhooks, schema, Mini App architecture, product changes beyond this test tour.
