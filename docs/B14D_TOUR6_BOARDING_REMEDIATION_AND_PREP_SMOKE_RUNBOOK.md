# B14D — Tour #6 boarding remediation & reservation-prep smoke (ops runbook)

**Project:** Tours_BOT. **Type:** operator documentation — **not** executed by doc authoring; **no** production mutation from Cursor/README alone.

**Refs:** **[`docs/B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md`](B14A_CHANNEL_LINK_AND_RESERVATION_READINESS_DIAGNOSTIC.md)** · **[`docs/HANDOFF_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT_TO_NEXT_STEP.md`](HANDOFF_B14C_TOUR_BOARDING_AND_PREP_ALIGNMENT_TO_NEXT_STEP.md)**

---

## 1. Safety (non-negotiable)

- **Environment:** production (or staging if rehearsing) — operator-owned.
- **Read-only first:** health, admin reads, Mini App **`GET …/preparation`** before any write.
- **Allowed write (if needed):** add **one or more** `boarding_points` rows for **Tour #6** only — align with **`AdminBoardingPointCreate`** (see §4 Option A).
- **Do not:** publish / retry / resend showcase; mutate **execution links**; create **orders**, **reservations**, or **payments**; run destructive SQL.
- **Reservation UI:** verify preparation opens; **do not** complete a real hold/checkout unless product explicitly approves.
- **Secrets:** do **not** paste **`ADMIN_API_TOKEN`** into tickets or screenshots; rotate in Railway if exposed (**[`docs/B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md`](B13G_PRODUCTION_PUBLISH_AUDIT_SMOKE_RUNBOOK.md)**).

---

## 2. Known IDs (smoke context)

| Field | Value |
|--------|--------|
| **supplier_offer_id** | **12** |
| **tour_id** | **6** |
| **tour_code** | **`B10-SO12-04fb1f`** |
| **execution_link_id** (recorded) | **5** |

---

## 3. Read-only checks (PowerShell)

Set **your** public API base (same host as Mini App and admin HTTP). Examples use **`$Base`** and **`$AdminToken`** (from env or secret store).

```powershell
$Base = "https://YOUR-RAILWAY_PUBLIC_HOST"   # no trailing slash
$AdminToken = $env:ADMIN_API_TOKEN           # or paste locally; do not commit
$HAdmin = @{ Authorization = "Bearer $AdminToken" }
```

### 3.1 Health / DB readiness

```powershell
Invoke-RestMethod -Uri "$Base/healthz" -Method Get
```

Expect **`status`** **`ready`** (or your deployment’s equivalent).

### 3.2 Supplier offer review-package (Offer #12)

```powershell
Invoke-RestMethod -Uri "$Base/admin/supplier-offers/12/review-package" -Headers $HAdmin -Method Get
```

Confirm JSON slices (illustrative keys): **`linked_tour_catalog`**, **`execution_links_review`**, **`conversion_status_panel`**, **`showcase`**, **`active_tour_bridge`**.  
Sanity: **`conversion_status_panel.booking_link.status`** = **`active`**, **`customer_action.status`** = **`open_exact_mini_app_tour`** (as in B13G).

### 3.3 Admin tour detail — **Tour #6** boarding list

```powershell
$t6 = Invoke-RestMethod -Uri "$Base/admin/tours/6" -Headers $HAdmin -Method Get
$t6.boarding_points
$t6.departure_datetime
```

- If **`boarding_points`** is **`@()`** / empty → **per_seat** prep will stay blocked until remediation (B14A/B14C).
- Copy **`departure_datetime`** → use its **local time** for **`time`** when creating a boarding row (§4).

### 3.4 Mini App — preparation (no admin auth)

```powershell
Invoke-RestMethod -Uri "$Base/mini-app/tours/B10-SO12-04fb1f/preparation" -Method Get
```

- **Before fix:** expect **HTTP 404** with detail **`tour is not available for reservation preparation`** (if boarding still missing).
- Optional query: `?language_code=en` (or first supported catalog language).

### 3.5 Supplier offer boarding source (for labels)

```powershell
Invoke-RestMethod -Uri "$Base/admin/supplier-offers/12" -Headers $HAdmin -Method Get
# Use `boarding_places_text` and title for factual `city` values on POST boarding-points
```

---

## 4. Boarding remediation options (code-inspected)

### Option A — **Preferred: existing admin API** (**implemented**)

**Endpoint:** **`POST /admin/tours/{tour_id}/boarding-points`**  
**Auth:** **`Authorization: Bearer <ADMIN_API_TOKEN>`** (same as other **`/admin`** routes — **`require_admin_api_token`**).  
**Schema:** **`AdminBoardingPointCreate`** — **`city`**, **`address`**, **`time`** (clock time), optional **`notes`**.

Code reference:

```126:132:app/schemas/admin.py
class AdminBoardingPointCreate(BaseModel):
    """Create one boarding stop for a tour (admin-only)."""

    city: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=255)
    time: time_type
    notes: str | None = None
```

**Procedure:**

1. From §3.3, read **`departure_datetime`** for Tour **6** (e.g. `2026-10-01T08:00:00+00:00` → use **`08:00:00`** in **`Europe/Bucharest`** context if ops align stops to published departure; if the API stores UTC, convert mentally or use the **same calendar time** you want customers to see — **be consistent** with tour publishing).
2. Set **`city`** from **Offer #12** **`boarding_places_text`** / known facts (e.g. *Timișoara* / first stop). ASCII *Timisoara* is acceptable if JSON tooling mangles diacritics.
3. Set **`address`** to a neutral line, e.g. **`As published in the tour / program`** (matches B14C materialization style).
4. **`notes`:** **`B14D remediation for Offer #12 smoke`**.

**PowerShell example** (adjust **`time`** to match **`GET /admin/tours/6`**):

```powershell
$body = @'
{
  "city": "Timisoara",
  "address": "As published in the tour / program",
  "time": "08:00:00",
  "notes": "B14D remediation for Offer #12 smoke"
}
'@
Invoke-RestMethod -Uri "$Base/admin/tours/6/boarding-points" -Headers $HAdmin -Method Post -Body $body -ContentType "application/json"
```

Response **`201`** with **`AdminTourDetailRead`** — confirm **`boarding_points`** length ≥ 1.

**Second stop:** if Offer #12 lists multiple places (e.g. `A | B`), repeat **`POST`** with the second **`city`** and same or adjusted **`time`** per ops policy.

---

### Option B — **Railway / psql** (fallback only)

Use **only** if admin API is unreachable and **DB access** is approved. Align columns with ORM **`BoardingPoint`**: **`tour_id`**, **`city`**, **`address`**, **`time`**, **`notes`** (nullable). **No** latitude/longitude columns.

- Prefer **Option A** for validation and audit (**FastAPI** validates lengths and non-blank **`city`**/**`address`**).
- If you must INSERT manually, match **`tours.departure_datetime`** time component for the default stop, **or** document the operator time choice.

*(Exact SQL is intentionally omitted here — vary by deployment; have a DBA verify FK **`tour_id=6`** and types.)*

---

### Option C — **Stop**

If neither API nor approved DB path is available: **do not** patch data ad hoc — ship a **small admin script** / ticket to run from a controlled environment.

---

## 5. Post-remediation smoke

### 5.1 API

```powershell
Invoke-RestMethod -Uri "$Base/admin/tours/6" -Headers $HAdmin -Method Get | Select-Object -ExpandProperty boarding_points
Invoke-RestMethod -Uri "$Base/mini-app/tours/B10-SO12-04fb1f/preparation" -Method Get
```

- Preparation should return **200** and a body with **`boarding_points`**, **`seat_count_options`** non-empty for **`per_seat`**, **`tour`**, **`sales_mode_policy`** (shape: **`MiniAppReservationPreparationRead`**).

### 5.2 Mini App UI (manual)

- Open exact tour **`B10-SO12-04fb1f`** → **Rezervă locuri** / reservation prep.
- **Expect:** preparation screen loads (seat/boarding UI) — **not** **`tour is not available for reservation preparation`**.
- **Do not** confirm booking unless explicitly approved.

### 5.3 Regression guard (read-only)

```powershell
Invoke-RestMethod -Uri "$Base/admin/supplier-offers/12/review-package" -Headers $HAdmin -Method Get | Out-Null
```

No change expected to **execution link** / **publish** from boarding-only writes.

---

## 6. Result recording template

| Field | Value |
|--------|--------|
| **Timestamp (UTC)** | |
| **Operator** | |
| **Environment** | production / staging |
| **Action** | read-only only / POST boarding / other (describe) |
| **Endpoint** | e.g. `POST /admin/tours/6/boarding-points` |
| **Boarding before** | count = |
| **Boarding after** | count = |
| **`GET …/preparation` before** | HTTP status / detail |
| **`GET …/preparation` after** | HTTP status |
| **Mini App prep UI** | opened / still blocked |
| **Reservation created** | **no** (unless explicitly approved) |
| **Notes** | |

---

## 7. Forward references

- **B14C (code):** **`app/services/supplier_offer_tour_bridge_service.py`** — future bridges materialize boarding from offer text.
- **Prep gate:** **`app/bot/services.py`** — **`PrivateReservationPreparationService.get_preparable_tour`**.
- **Mini App:** **`GET /mini-app/tours/{tour_code}/preparation`** — **`app/api/routes/mini_app.py`**.
