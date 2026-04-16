# Commit / push / deploy — Phase 7.1 (Sales Mode)

Two narrow slices: **Step 1** (admin + migration) and **Step 2** (backend policy — **no** migration).

**Handoff / continuity:** `docs/CHAT_HANDOFF.md` (**Current continuity state**, **Completed Steps** → Phase **7.1**, **Next Safe Step**).

---

# Part A — Step 1 (frozen)

Operational notes for **admin/source-of-truth** `tour.sales_mode` only.  
**Not** booking, payment, Mini App, private bot, or whole-bus flows.

---

## A1. Step identity

- **Phase 7.1 / Sales Mode / Step 1** — **finalized / frozen** (no further Step **1** scope without a new explicit slice).
- **Narrow admin/source-of-truth slice only** — `TourSalesMode`, `Tour.sales_mode`, admin read/write + Alembic migration; **no** customer-facing behavior change.

---

## A2. What changed

- **`TourSalesMode`** enum: `per_seat`, `full_bus` (`app/models/enums.py`).
- **`Tour.sales_mode`** on ORM model with safe default **`per_seat`** (`app/models/tour.py`).
- **Admin schemas** — list/detail/create/patch expose `sales_mode` (`app/schemas/admin.py`).
- **Admin read** — `GET /admin/tours`, `GET /admin/tours/{id}` include `sales_mode` (`app/services/admin_read.py`).
- **Admin write** — `POST /admin/tours`, `PATCH /admin/tours/{id}` persist `sales_mode` (`app/services/admin_tour_write.py`).
- **Migration** — `alembic/versions/20260416_06_add_tour_sales_mode.py`: Postgres enum `tour_sales_mode` + `tours.sales_mode` NOT NULL, server default `per_seat`.
- **Tests** — focused `sales_mode` + narrow adjacent admin tour cases (`tests/unit/test_api_admin.py`).
- **Freeze verification (test hygiene only):** `test_post_admin_order_move_rejects_target_not_open_for_sale` uses **Aug 2026** departures so the case still hits **`order_move_target_tour_not_open_for_sale`** after wall-clock passes early **Apr 2026** (otherwise Step **28** readiness returns **`order_move_not_ready`** first). **No** product or move-policy change.

### Files changed

- `app/models/enums.py`
- `app/models/tour.py`
- `app/schemas/admin.py`
- `app/services/admin_read.py`
- `app/services/admin_tour_write.py`
- `tests/unit/test_api_admin.py`

### File added

- `alembic/versions/20260416_06_add_tour_sales_mode.py`

### Tests already run (reference)

- `python -m alembic upgrade head`
- `python -m pytest tests/unit/test_api_admin.py -k sales_mode` → **4 passed**
- `python -m pytest tests/unit/test_api_admin.py -k "post_admin_tour_success_and_seats_available or patch_admin_tour_core_success or put_admin_tour_cover_success_and_get_detail"` → **3 passed**

---

## A3. What did NOT change

- **Booking logic** — reservation creation, order totals, seat holds unchanged.
- **Payment logic** — reconciliation, webhooks, payment entry unchanged.
- **Mini App behavior** — catalog, booking, payment surfaces unchanged.
- **Private bot behavior** — handlers, copy, flows unchanged.
- **Operator / Phase 7 handoff** — `group_followup_*`, admin handoff mutations unchanged.
- **Direct whole-bus booking** — not implemented.
- **Seat / availability semantics** — `seats_total` / `seats_available` rules unchanged; `sales_mode` does not alter inventory math in this step.

---

## A4. Pre-commit checklist

Run from repo root (use project venv if applicable):

1. `python -m compileall app alembic tests`
2. `python -m alembic current`
3. `python -m alembic heads` — expect head revision **`20260416_06`** (or your merged chain tip after this migration).
4. **Optional but recommended** (clean DB / dev only): `python -m alembic downgrade -1` then `python -m alembic upgrade head` — confirms migration applies idempotently.
5. `python -m pytest tests/unit/test_api_admin.py -v` — or at minimum the two focused commands in §A2.
6. `uvicorn app.main:app --reload` (local smoke).
7. Verify **`GET /health`** returns OK.
8. Verify **`GET /healthz`** returns OK.

**Stage only** the files listed in §A2 (plus this doc if you version it). Do **not** bundle unrelated doc churn unless intentionally in the same release.

---

## A5. Suggested commit message

Pick one (Conventional Commits style):

1. `feat(admin): add tour sales_mode source-of-truth (phase 7.1 step 1)`
2. `feat: add admin sales_mode for tours and migration 20260416_06`
3. `feat: phase 7.1 sales mode step 1 — tour.sales_mode + alembic`

---

## A6. Push steps

1. `git status` — confirm only intended paths.
2. `git add app/models/enums.py app/models/tour.py app/schemas/admin.py app/services/admin_read.py app/services/admin_tour_write.py tests/unit/test_api_admin.py alembic/versions/20260416_06_add_tour_sales_mode.py`
3. Optionally (handoff / deploy freeze): `git add COMMIT_PUSH_DEPLOY.md docs/CHAT_HANDOFF.md`
4. `git commit -m "<message from §A5>"`
5. `git push` (current branch, e.g. `main` or feature branch per team practice).

---

## A7. Deploy / migration notes

- **This step includes a DB migration** — deploy **must** run **`alembic upgrade head`** (or equivalent) **before or with** the app version that loads `Tour` with `sales_mode`, or you risk **`UndefinedColumn`** on any code path that selects `tours.*`.
- **Existing tours** — column backfill uses **`server_default=per_seat`**; all existing rows should land on **`per_seat`**.
- **After deploy** — confirm admin **`GET /admin/tours`**, **`GET /admin/tours/{id}`**, **`POST /admin/tours`**, **`PATCH /admin/tours/{id}`** still work and return **`sales_mode`**.

---

## A8. Post-deploy smoke

- App starts; no crash on import/ORM.
- **`GET /health`** — OK.
- **`GET /healthz`** — OK.
- **`alembic current`** on target DB — matches **`heads`** (includes **`20260416_06`**).
- **Admin** (with token): list tours — each item has **`sales_mode`**.
- **Admin**: get tour detail — **`sales_mode`** present; legacy data shows **`per_seat`**.
- **Admin**: create tour with **`sales_mode": "full_bus"`** (optional) — persists and reads back.
- **Admin**: patch existing tour **`sales_mode`** — persists.

---

## A9. Rollback note

- **Code rollback** without DB downgrade leaves schema ahead of code (usually tolerable) or code ahead of schema (breaks). Prefer **coordinated** revert.
- If **full rollback**: revert the commit, then **`python -m alembic downgrade`** to the revision **before** `20260416_06` **only if** no **later** migration depends on `tour_sales_mode` / `tours.sales_mode`. Check `alembic history` / `heads` first.
- Dropping enum `tour_sales_mode` may require the column removed first; follow the migration’s **`downgrade()`** order.

---

## A10. Explicitly postponed (Step 1 only)

- **`full_bus_price`**
- **`bus_capacity`**
- **Mini App** read-side / UX adaptation (see **Part B** / Step **3** in handoff)
- **Private bot** read-side / UX adaptation
- **Operator-assisted** full-bus path
- **Direct** whole-bus booking flow

---

# Part B — Step 2 (backend policy)

**No database migration.** Code-only slice: centralized interpretation of existing **`tour.sales_mode`**. **No** customer API or UI behavior change.

---

## B1. Step identity

- **Phase 7.1 / Sales Mode / Step 2** — backend **`TourSalesModePolicyService`** + **`TourSalesModePolicyRead`**.
- Policy is derived **only** from **`TourSalesMode`** (persisted on **`tours.sales_mode`** — Step **1** source of truth). **Not** from seat counts.

---

## B2. What changed

- **`TourSalesModePolicyRead`** — `app/schemas/tour_sales_mode_policy.py` (frozen Pydantic: `effective_sales_mode`, `per_seat_self_service_allowed`, `direct_customer_booking_blocked_or_deferred`, `operator_path_required`).
- **`TourSalesModePolicyService`** — `app/services/tour_sales_mode_policy.py` (`policy_for_sales_mode`, `policy_for_tour`).
- **Tests** — `tests/unit/test_tour_sales_mode_policy.py` (incl. unwired **`reservation_creation`** / **`mini_app_booking`** guard).

### Files added

- `app/schemas/tour_sales_mode_policy.py`
- `app/services/tour_sales_mode_policy.py`
- `tests/unit/test_tour_sales_mode_policy.py`

### Scope confirmation

- **`tour.sales_mode`** remains the **only** commercial mode source of truth.
- **No** Mini App / private bot / reservation / payment / Phase **7** handoff edits in Step **2**.
- **No** direct whole-bus booking; **no** operator-assisted whole-bus path.

---

## B3. What did NOT change

Same non-goals as Step **1** for customer-visible behavior: booking creation semantics, payment, Mini App flows, private bot flows, operator handoff chain, seat inventory rules.

---

## B4. Pre-commit / pre-push checklist

1. `python -m compileall app tests`
2. `python -m pytest tests/unit/test_tour_sales_mode_policy.py -v`
3. **Recommended regression:** `python -m pytest tests/unit/test_api_admin.py -k sales_mode -q` (admin field unchanged)
4. `uvicorn app.main:app --reload` — **`GET /health`**, **`GET /healthz`**

**No** `alembic upgrade` required for Step **2** alone (unless combined with unreleased Step **1** migration on an environment).

---

## B5. Suggested commit message

1. `feat: add TourSalesModePolicyService for tour sales mode (phase 7.1 step 2)`
2. `feat(policy): centralize per_seat/full_bus interpretation (phase 7.1.2)`

---

## B6. Push steps

1. `git add app/schemas/tour_sales_mode_policy.py app/services/tour_sales_mode_policy.py tests/unit/test_tour_sales_mode_policy.py`
2. Optionally: `git add docs/CHAT_HANDOFF.md docs/OPEN_QUESTIONS_AND_TECH_DEBT.md COMMIT_PUSH_DEPLOY.md`
3. `git commit -m "<message from B5>"` && `git push`

---

## B7. Deploy notes

- **Schema:** unchanged by Step **2**.
- **Risk:** low — new modules only; ensure Step **1** migration already applied on DBs that run ORM with **`Tour.sales_mode`**.

---

## B8. Post-deploy smoke

- App starts; **`/health`**, **`/healthz`** OK.
- (Optional) Run **`tests/unit/test_tour_sales_mode_policy.py`** in CI.
- **No** change expected on Mini App or bot booking paths.

---

## B9. Rollback

- Revert the Step **2** commit(s). **No** Alembic downgrade tied to this slice.

---

## B10. Explicitly postponed (not Step 2)

- **Step 3** — Mini App + private bot **read-side** adaptation
- **Reservation enforcement** for **`full_bus`**
- **`full_bus_price`**, **`bus_capacity`**
- Operator-assisted / direct whole-bus booking

---

*Design reference: `docs/TOUR_SALES_MODE_DESIGN.md`. Handoff: `docs/CHAT_HANDOFF.md`. Tech debt / status: `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` §20.*
