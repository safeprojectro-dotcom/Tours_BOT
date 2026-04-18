# Commit / push / deploy — Phase 7.1 (Sales Mode)

Operational checkpoints in this file: **Part A — Step 1** (admin + migration **`20260416_06`**); **Part B — Step 2** (backend policy — **no** migration); **Part C — Step 5** (operator-assisted full-bus path — structured handoff **`reason`** — **no** migration).

**Handoff / continuity:** `docs/CHAT_HANDOFF.md` (**Current continuity state**, **Completed Steps** → Phase **7.1**, **Next Safe Step**).

**V2 supplier marketplace — Track 0 (freeze):** before/after each future V2 track that touches booking, payments, ORM, Mini App, or bot, run the **must-not-break checklist** and **baseline smoke** in **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`**. Track **0** does **not** add features; it only documents compatibility and deploy guardrails.

**V2 Track 1 (design acceptance):** documentation gate complete — see **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`**. **Track 2+** implementation must still obey **migrate → deploy → smoke** and Track **0** §4–§5.

**V2 Track 2 (Supplier Admin Foundation):** adds Alembic revision **`20260417_07`** (`suppliers`, `supplier_api_credentials`, `supplier_offers`, new enums; **no** DDL changes to **`tours`**, **`orders`**, or **`payments`**). **Do not** deploy application code that imports or routes to these models until **`python -m alembic upgrade head`** has been run on the target database (verify **`alembic current`** matches **`heads`**). After deploy, smoke **`/health`**, existing **`/mini-app/*`** catalog/booking paths, and **new** **`/admin/suppliers`** / **`/supplier-admin/offers`** if that environment uses Layer B. **Schema drift** on Track **2** surfaces as missing-relation errors on supplier routes, not necessarily on core catalog — still a release blocker. Details: **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §17, §23.

**V2 Track 3 (Supplier offer publication / moderation):** adds Alembic revision **`20260418_08`** (extends **`supplier_offer_lifecycle`** with **`approved`**, **`rejected`**, **`published`**; adds moderation/showcase columns on **`supplier_offers`**). **Env:** optional **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`** (and existing **`TELEGRAM_BOT_TOKEN`**, **`TELEGRAM_BOT_USERNAME`**, **`TELEGRAM_MINI_APP_URL`**) required for **`POST /admin/supplier-offers/{id}/publish`** to succeed. Same **migrate → deploy → smoke** gate; verify **`heads`** includes **`20260418_08`** when Track **3** code is deployed. **Stabilization:** publication is **admin-only** and **`publish`** requires **`approved`**; suppliers have **no** channel post path — see **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §24 and **`docs/CURSOR_PROMPT_TRACK_3_STABILIZATION_AND_REVIEW_V2.md`**.

**V2 Track 4 (Custom request marketplace / Layer C):** adds Alembic revision **`20260421_10`** (**`custom_marketplace_requests`**, **`supplier_custom_request_responses`**, new Postgres enums; **no** changes to **`tours`**, **`orders`**, **`payments`**). **Do not** deploy Track **4** application code until **`python -m alembic upgrade head`** on the target DB includes **`20260421_10`**. After deploy, smoke **`/health`**, core **`/mini-app/catalog`** (and booking paths if used), **`POST /mini-app/custom-requests`** (optional), **`/admin/custom-requests`**, and **`/supplier-admin/custom-requests`** if that environment uses Layer C. **Schema drift** surfaces as missing tables/enums on RFQ routes. **Stabilization:** RFQ is **not** an order lifecycle — see **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §25 and **`docs/CURSOR_PROMPT_TRACK_4_STABILIZATION_AND_REVIEW_V2.md`**.

**V2 Track 5b.1 (RFQ booking bridge record / Layer C):** adds Alembic revision **`20260423_12`** (table **`custom_request_booking_bridges`**, enum **`custom_request_booking_bridge_status`**; **no** `orders`/`payments` DDL). Bridge rows are **execution intent only** — **no** reservation or payment. Deploy only after migration; smoke admin **`GET/PATCH/POST .../custom-requests/.../booking-bridge`** as needed. **Stabilization review** recorded in **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §27 (closure subsection). See **`docs/CHAT_HANDOFF.md`** (Track **5b.1** bullet).

**V2 Track 5b.2 (RFQ bridge execution entry):** **no** new Alembic revision — Mini App **`GET/POST /mini-app/custom-requests/{id}/booking-bridge/preparation`** and **`.../reservations`** only. Reuses existing Layer A hold service; **no** new payment path. Smoke with **`20260423_12`** applied: bridge + linked tour + **`supplier_selected`** request, then customer preparation/reservation. **Stabilization review** recorded in **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §28 (closure subsection). See **`docs/CHAT_HANDOFF.md`** (Track **5b.2** bullet).

**V2 Track 5b.3a (RFQ supplier policy + effective execution resolver):** adds Alembic revision **`20260424_13`** — nullable **`supplier_declared_sales_mode`** and **`supplier_declared_payment_mode`** on **`supplier_custom_request_responses`** (reuse enums **`tour_sales_mode`**, **`supplier_offer_payment_mode`**). **Proposed** supplier responses **must** declare both fields (validated); **`full_bus` + `platform_checkout`** rejected. **`EffectiveCommercialExecutionPolicyService`** composes **`TourSalesModePolicyService`**, supplier declaration, and Track **5a** external resolution signals; Track **5b.2** bridge execution uses this resolver (not tour-only). **No** payment sessions or checkout changes. Deploy after migration; smoke supplier **`PUT .../response`**, admin request detail **`effective_execution_policy`** when bridge has **`tour_id`**, and bridge preparation/reservation. **Stabilization review:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §29; **`docs/CHAT_HANDOFF.md`** (Track **5b.3a** bullet).

**V2 Track 5b.3b (bridge payment eligibility + existing payment-entry):** **no** new Alembic revision. Adds **`GET /mini-app/custom-requests/{id}/booking-bridge/payment-eligibility`** (`telegram_user_id`, **`order_id`**) — read-only gate; **no** payment rows created. When **`payment_entry_allowed`**, client continues with **existing** **`POST /mini-app/orders/{order_id}/payment-entry`**. Smoke: bridge hold → eligibility → payment-entry (same as catalog payment path). **Stabilization review:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §30 (closure subsection); **`docs/CHAT_HANDOFF.md`** (Track **5b.3b** bullet).

**V2 Track 5c (RFQ Mini App UX wiring):** **no** new Alembic revision. Mini App navigates to **`/custom-requests/{id}/bridge`** and uses **existing** bridge **preparation** / **reservation** / **payment-eligibility** endpoints; payment session creation remains **only** **`POST /mini-app/orders/{order_id}/payment-entry`** after the usual **`open_payment_entry`** stack. Smoke: configured bridge + eligible tour → preparation → hold → eligibility **true** → payment-entry; assisted/blocked preparation → **no** reserve CTA; eligibility **false** with active hold → **no** pay CTA. **Stabilization review** recorded in **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §31 (closure subsection). **Record:** **`docs/CHAT_HANDOFF.md`** (Track **5c** bullet).

**V2 Track 5a (Commercial resolution selection / Layer C):** adds Alembic revision **`20260422_11`** (**extends** **`custom_marketplace_request_status`**, **`UPDATE` legacy `fulfilled` → `closed_assisted`**, new enum **`commercial_resolution_kind`**, columns **`selected_supplier_response_id`**, **`commercial_resolution_kind`** on **`custom_marketplace_requests`**; **still no** **`tours`/`orders`/`payments`** DDL). Migration uses **autocommit blocks** per **`ALTER TYPE ... ADD VALUE`** (PostgreSQL). **Do not** deploy Track **5a** code until **`20260422_11`** is applied on the target DB. Smoke **`/admin/custom-requests`**, **`POST /admin/custom-requests/{id}/resolution`** (auth), **`GET /mini-app/custom-requests`**, core catalog/booking paths, and **`/supplier-admin/custom-requests`** as needed. **Downgrade caveat:** enum labels added to **`custom_marketplace_request_status`** are **not** removed by Alembic downgrade — see migration comment and **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §26. **Stabilization:** **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** §26, **`docs/CHAT_HANDOFF.md`** (Track **5a** bullet).

---

## Dev/staging — smoke tour refresh (test data)

Manual Mini App / catalog smokes expect **future** `departure_datetime`, a future **`sales_deadline`**, and **`OPEN_FOR_SALE`** tours. When fixed demo codes drift into the past, refresh from repo root (valid **`DATABASE_URL`**; **dev/staging** or empty DBs — not for busy production if orders exist on these codes):

```bash
python -m app.scripts.ensure_smoke_tours
```

Optional env: **`SMOKE_TOURS_DAYS_AHEAD`** (default **`60`**, minimum **`2`**).

**Behavior:** **creates or updates** tours **`SMOKE_PER_SEAT_001`** (`per_seat`) and **`SMOKE_FULL_BUS_001`** (`full_bus`); adds a default **`boarding_points`** row if the tour has none; normalizes **seat counts** on those codes. **Implementation:** `app/scripts/ensure_smoke_tours.py` — **no** booking, payment, or marketplace logic changes.

---

## Deploy-critical — Phase 7.1 `tours.sales_mode` (Railway / staging / production)

**Confirmed failure when schema lags code:** deployed application code **SELECT**s **`tours.sales_mode`** (ORM + Phase **7.1**), but PostgreSQL had **not** applied Alembic revision **`20260416_06`** → **`psycopg.errors.UndefinedColumn: column tours.sales_mode does not exist`**. **Root cause:** the migration was **not** applied to the target database before or with the deploy that shipped that code — **schema drift**, not application “logic bugs.”

**Requirement for any environment running Phase 7.1+ tour code:** run migrations **before** or **as part of** deploy so the DB matches `heads`, at minimum:

```bash
python -m alembic upgrade head
```

(Use a **reachable** `DATABASE_URL` for that environment — often the Railway **public** Postgres URL and a driver form such as **`postgresql+psycopg://...`** if running Alembic from a local shell.) **Do not** treat Mini App, private bot, or API fixes as the next step until **`alembic current`** on that database matches **`alembic heads`** (including **`20260416_06`**, **`20260417_07`**, **`20260418_08`**, **`20260419_09`**, **`20260421_10`**, **`20260422_11`**, **`20260423_12`**, **`20260424_13`** as applicable when V2 Track **2** / **3** / **3.1** (showcase polish) / **4** / **5a** / **5b.1** / **5b.3a** code is deployed). Then redeploy if needed and smoke **`/health`**, catalog, and any tour-loading routes.

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

- **This step includes a DB migration** — deploy **must** run **`python -m alembic upgrade head`** (or equivalent) **before or with** the app version that loads `Tour` with `sales_mode`, or you risk **`psycopg.errors.UndefinedColumn` / `column tours.sales_mode does not exist`** (and **`ProgrammingError`**) on **every** path that loads **`Tour`** — catalog, bookings, admin, bot, etc. **Skipping this step is a known production/staging incident pattern** (see **Deploy-critical** above).
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
- **Risk:** low for DDL — new modules only — but **runtime risk is high** if Step **1** was never applied: Step **2** and later Phase **7.1** code still **expects** **`tours.sales_mode`**. **Always** confirm **`python -m alembic upgrade head`** (or equivalent) has been run on the target DB **before** relying on any Phase **7.1** release there (see **Deploy-critical** at top of this doc).

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

- **Step 3** — Mini App + private bot **read-side** adaptation (historical at Step **2** closure; see **`docs/CHAT_HANDOFF.md`** for Steps **3–4** + **5**)
- **Reservation enforcement** for **`full_bus`**
- **`full_bus_price`**, **`bus_capacity`**
- **Direct** whole-bus **self-service** booking / payment *(Step **5** / **Part C** is **operator-assisted** handoff context only.)*

---

# Part C — Step 5 (operator-assisted full-bus path)

**No database migration.** Narrow slice: structured **`full_bus_sales_assistance`** context in **`handoffs.reason`**, tour-aware private bot + Mini App assistance entry points, admin read triage fields. **Not** direct whole-bus booking or payment.

---

## C1. Step identity

- **Phase 7.1 / Sales Mode / Step 5** — operator-assisted full-bus path (structured assistance / handoff **`reason`**).
- **No migration** — context is encoded in existing **`handoffs.reason`** (varchar **255**).

---

## C2. What changed

- **Structured assistance `reason`:** full-bus assistance uses a compact **`full_bus_sales_assistance|…`** encoding in **`handoffs.reason`** instead of only generic **`private_chat_contact`** / **`mini_app_support|…`** on those paths.
- **Private bot:** **Request booking assistance** callback is **tour-scoped**; when policy disallows per-seat self-service, persisted handoff **`reason`** includes **tour code** and **`sales_mode`** (**`channel=private`**).
- **Mini App:** optional **`tour_code`** on **`POST /mini-app/support-request`**; for non-self-service tours per policy, the same structured **`reason`** is used (**`channel=mini_app`**); assisted tour detail includes **Request full-bus assistance**.
- **Admin handoff DTOs** (list, detail, order-embedded **`handoffs`**): **`is_full_bus_sales_assistance`**, **`full_bus_sales_assistance_label`**, **`assistance_context_tour_code`** — triage without requiring **`order_id`**.

### Files changed

- `app/services/handoff_entry.py`
- `app/services/admin_handoff_queue.py`
- `app/schemas/admin.py`
- `app/services/admin_read.py`
- `app/bot/constants.py`
- `app/bot/keyboards.py`
- `app/bot/handlers/private_entry.py`
- `app/schemas/mini_app.py`
- `app/api/routes/mini_app.py`
- `mini_app/api_client.py`
- `mini_app/app.py`
- `mini_app/ui_strings.py`
- `tests/unit/test_handoff_entry.py`
- `tests/unit/test_admin_handoff_group_followup_visibility.py`
- `tests/unit/test_api_admin.py`
- `tests/unit/test_api_mini_app.py`
- `tests/unit/test_bot_private_foundation.py`

### Tests run (reference — focused slice, **passed**)

From repo root (venv if applicable):

```bash
python -m pytest tests/unit/test_handoff_entry.py tests/unit/test_admin_handoff_group_followup_visibility.py tests/unit/test_api_admin.py::AdminRouteTests::test_handoffs_list_no_order_stable_shape tests/unit/test_api_admin.py::AdminRouteTests::test_handoffs_list_full_bus_sales_assistance_exposes_context tests/unit/test_api_mini_app.py::MiniAppCatalogRouteTests::test_support_request_with_full_bus_tour_code_uses_structured_reason tests/unit/test_api_mini_app.py::MiniAppCatalogRouteTests::test_support_request_per_seat_tour_code_stays_generic_mini_app tests/unit/test_bot_private_foundation.py::PrivateBotSalesModeReadTests::test_tour_detail_keyboard_prepare_vs_assistance -q
```

**Result:** **39 passed** (includes full **`test_handoff_entry`** and **`test_admin_handoff_group_followup_visibility`** modules in that invocation).

**Optional broader check:** `python -m pytest tests/unit -q`

---

## C3. What did NOT change

- **Direct whole-bus booking** — no self-service whole-bus reservation flow.
- **Whole-bus payment** — no new payment path for charter/full-bus checkout.
- **`TemporaryReservationService`** — not modified for this step.
- **`reservation_creation.py`** — not modified for this step.
- **Pricing engine** — no **`full_bus_price`** or commercial pricing expansion.
- **Capacity model** — no **`bus_capacity`** or inventory semantics change.
- **Broad operator workflow** — no Phase **7** **`grp_followup_*`** rewrite; no separate operator subsystem.
- **Alembic / DDL** — no new revision for Step **5**.

---

## C4. Pre-commit checklist

1. `python -m compileall app alembic tests`
2. Run the focused pytest command in **§C2** (or full `tests/unit` if policy requires).
3. If environment allows: `uvicorn app.main:app --reload` — **`GET /health`**, **`GET /healthz`** OK.
4. Confirm **no migration** is required for Step **5** alone — target DB must **already** have **`tours.sales_mode`** (**Part A** / **`20260416_06`**) for Phase **7.1** code to run safely (see **Deploy-critical** at top).

---

## C5. Suggested commit message

1. `feat(handoff): add structured full-bus assistance context`
2. `feat: complete phase 7.1 operator-assisted full-bus path`
3. `feat(admin): expose structured full-bus assistance context`

---

## C6. Push steps

1. `git status` — confirm only intended paths (see **§C2** file list + any doc updates).
2. `git add` the Step **5** files (adjust if paths differ).
3. `git commit -m "<message from §C5>"`
4. `git push` (current branch per team practice).

---

## C7. Deploy notes

- **No new migration** in Step **5** — deploy **does not** add Alembic revisions for this slice.
- **Prerequisite:** target environment must **already** have Phase **7.1** **`tours.sales_mode`** DDL applied (**`20260416_06`** or later per **`alembic heads`**) — same **Deploy-critical** gate as existing Phase **7.1** releases.
- After deploy: verify **private bot**, **Mini App**, and **admin** handoff reads behave as expected (see **§C8**).

---

## C8. Post-deploy smoke

- **Private bot:** open a **`full_bus`** tour → **Request booking assistance** → handoff row **`reason`** starts with **`full_bus_sales_assistance`** (not only **`private_chat_contact`** when tour/policy path applies).
- **Mini App:** **`full_bus`** tour detail → **Request full-bus assistance** (or **`POST /mini-app/support-request`** with **`tour_code`**) → structured **`reason`** with **`channel=mini_app`**.
- **Admin:** **`GET /admin/handoffs`** / detail — **`is_full_bus_sales_assistance`** true and **`assistance_context_tour_code`** set for those rows; **`full_bus_sales_assistance_label`** present.
- **Per-seat:** **`per_seat`** tours — self-service and generic **`mini_app_support|…`** support requests **unchanged**; no regression on prepare/reservation where policy allows.

---

## C9. Rollback note

- Revert the Step **5** commit(s) (code only). **No** Alembic downgrade tied to this slice.
- Rollback **only** removes structured **`reason`** encoding and admin triage fields — existing **`handoffs`** rows written with **`full_bus_sales_assistance`** may remain in DB until closed/archived; operators should expect older clients not to show **`is_full_bus_sales_assistance`** if reverted.

---

## C10. Explicitly postponed (Step 5+ / product)

- **Direct whole-bus reservation flow**
- **Whole-bus payment flow**
- **`full_bus_price`**, **`bus_capacity`**
- **Pricing expansion**
- **`TemporaryReservationService` / reservation engine refactor**
- **Broad operator workflow rewrite**
- Any **“many seats ⇒ whole bus”** heuristic

---

*Design reference: `docs/TOUR_SALES_MODE_DESIGN.md`. Handoff: `docs/CHAT_HANDOFF.md`. Tech debt / status: `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` §20.*
