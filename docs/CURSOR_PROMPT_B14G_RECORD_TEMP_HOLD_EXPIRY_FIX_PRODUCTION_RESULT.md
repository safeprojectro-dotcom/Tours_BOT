# CURSOR_PROMPT_B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT

Record the B14F production verification result.

This is docs-only. Do not change application code.

## Context

B14F implemented:

- `lazy_expire_due_reservations_commit_if_any`
- committing lazy-expiry paths for:
  - catalog
  - tour detail
  - bookings list/detail
  - reservation overview
  - payment entry
  - preparation gate
  - bot/private prep

B14F was committed and pushed:

- commit: `58968a5`
- message: `fix: persist lazy reservation expiry`

Production smoke IDs:

- Supplier Offer #12
- Tour #6
- tour_code: `B10-SO12-04fb1f`
- execution_link_id: 5
- boarding_point_id: 15
- smoke orders:
  - Order #52, seats_count = 1
  - Order #53, seats_count = 2
  - Order #53 has open handoff #86

Before B14F production verification:

- Tour #6 seats_total = 10
- Tour #6 seats_available = 7
- Order #52 lifecycle_kind = `active_temporary_hold`
- Order #53 lifecycle_kind = `active_temporary_hold`
- Both were past `reservation_expires_at`

After B14F deploy, operator triggered:

```powershell
$TourCode = "B10-SO12-04fb1f"

Invoke-RestMethod `
  -Uri "$Base/mini-app/tours/$TourCode/preparation" `
  -Method GET | ConvertTo-Json -Depth 5
```

## Deliverable

- **`docs/B14G_RECORD_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_RESULT.md`** — run log; **§6** documents **PASS** (operator-verified metrics).
- **`docs/HANDOFF_B14G_TEMP_HOLD_EXPIRY_FIX_PRODUCTION_VERIFICATION_TO_NEXT_STEP.md`** — production verification handoff (checkpoint, closed / open, next prompts).
- Updates to **`docs/CHAT_HANDOFF.md`** and **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** (B14G pointer / verification status).

**Docs-only.** No application code.