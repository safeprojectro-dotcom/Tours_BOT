# HANDOFF_B14D_TOUR6_BOARDING_REMEDIATION_AND_PREP_SMOKE_TO_NEXT_STEP

## Checkpoint

**B14C** fixed **future** bridge-created tours by materializing **`boarding_points`** from supplier offer **`boarding_places_text`**.

**Existing** production **Tour #6** / **`B10-SO12-04fb1f`** was created **before** B14C and may still lack boarding rows — blocking **`per_seat`** reservation preparation per **B14A**.

## B14D purpose

Prepare a **production-safe runbook** to:

1. Verify Tour **#6** boarding points (**read-only** first).
2. Add a **minimal** boarding point **only if** missing (prefer **`POST /admin/tours/6/boarding-points`**).
3. Re-check Mini App **`GET /mini-app/tours/B10-SO12-04fb1f/preparation`**.
4. Confirm **Rezervă locuri** / prep flow no longer surfaces **`tour is not available for reservation preparation`** (UI + API).
5. **Do not** complete a real reservation unless explicitly approved.

**Canonical runbook:** **[`docs/B14D_TOUR6_BOARDING_REMEDIATION_AND_PREP_SMOKE_RUNBOOK.md`](B14D_TOUR6_BOARDING_REMEDIATION_AND_PREP_SMOKE_RUNBOOK.md)**

## Safety

- **Docs / ops guidance** in repo; **operators** execute in prod/staging.
- **No** app code / tests / migrations from this track.
- **No** production API calls or data mutation **from Cursor** during doc work.
- **No** publish / retry / resend; **no** execution-link mutation; **no** orders / payments / reservations unless product explicitly approves beyond prep smoke.

## Code inspection outcome (B14D authoring)

**Preferred path:** **`POST /admin/tours/{tour_id}/boarding-points`** with **`AdminBoardingPointCreate`** (`city`, `address`, `time`, optional `notes`), **`Authorization: Bearer ADMIN_API_TOKEN`**. See **`app/api/routes/admin.py`**, **`app/schemas/admin.py`**.

**Fallback:** DBA-approved **`boarding_points`** INSERT if API unavailable — runbook **Option B** (no ad-hoc SQL in Cursor).

## Next operator action

After the **B14D** runbook is available in your deploy branch:

1. **Rotate** **`ADMIN_API_TOKEN`** in Railway if not already done (post-smoke hygiene).
2. Run runbook **§3** **read-only** checks (`/healthz`, **`GET /admin/tours/6`**, **`GET …/preparation`**).
3. If boarding is missing → runbook **§4 Option A** **POST** boarding for **`tour_id=6`**.
4. Re-test Mini App preparation (**§5**); record **§6** template.
5. **Reservation created:** default **no** unless explicitly approved.

## Status

**Runbook prepared** — **remediation execution not claimed** until operators record results in **§6** of the runbook.

## References

- Diagnostic: **[`docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md`](B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md)**
- B14C handoff: **[`docs/HANDOFF_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT_TO_NEXT_STEP.md`](HANDOFF_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT_TO_NEXT_STEP.md)**
- Continuity: **[`docs/CHAT_HANDOFF.md`](CHAT_HANDOFF.md)** (B14D bullet)
- Debt line: **[`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`](OPEN_QUESTIONS_AND_TECH_DEBT.md)** (Layer A / Tour #6)
