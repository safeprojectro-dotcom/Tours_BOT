# Chat Handoff

## Project
Tours_BOT

## Current Status
The project is ready to continue from the **latest approved checkpoint**: **Phase 6 / Step 18 completed** — **read-only** admin **handoff queue** visibility: **`GET /admin/handoffs`**, **`GET /admin/handoffs/{handoff_id}`** (**no** schema migration). Response includes persisted fields (status, reason, priority, ids, timestamps) plus queue-oriented signals **`is_open`**, **`needs_attention`**, **`age_bucket`** (see **`app/services/admin_handoff_queue.py`**). **Still not in admin:** handoff **claim/assign/close** (see **Next Safe Step**). **No** public catalog / Mini App changes; public booking/payment/waitlist/**customer** handoff creation flows **unchanged**.

**Phase 6 / Steps 1–18** (completed): **`ADMIN_API_TOKEN`**; tours, boarding, tour/boarding **translations**, archive/unarchive; orders with Step **16** correction + Step **17** action preview; **handoff list/detail** read API.

Earlier: **Phase 5 (Mini App MVP) accepted** for MVP/staging; **Phase 5 / Step 20** documentation consolidation (`docs/PHASE_5_ACCEPTANCE_SUMMARY.md`). No Phase 5 MVP blockers for the agreed scope.

**Next work:** **Phase 6 / Step 19** — **first narrow admin handoff status mutation slice** (product-approved rules only) — see **Next Safe Step**.

### Operational note (production — Step 6 schema recovery)
After Step 6 backend shipped to Railway **before** production Postgres had applied Alembic revision **`20260405_04`**, the missing column **`tours.cover_media_reference`** caused **`ProgrammingError` / `UndefinedColumn`** and **500**s on routes that load tours (e.g. **`/mini-app/catalog`**, **`/mini-app/bookings`**). Root cause was **schema mismatch**, not Mini App UI logic. **Recovery completed:** migrations applied against the Railway DB (using the **public** Postgres URL and a local driver URL such as **`postgresql+psycopg://...`** where internal hostnames are not resolvable), backend **redeployed**, **`/health`**, catalog, and bookings smoke-checked. **Going forward:** any schema-changing step must include **migration apply → redeploy → smoke** for affected endpoints. Details: **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` section 17**.

## Current Phase

**Current phase (forward work):** **Phase 6 — Admin Panel MVP** — **Phase 6 / Steps 1–18 completed.**

**Latest approved checkpoint:** **Phase 6 / Step 18** — admin **handoff queue** **list + detail** (**`GET /admin/handoffs`**, **`GET /admin/handoffs/{handoff_id}`**); order detail still carries Steps **16–17**. **Still not implemented via `/admin/*`:** handoff **claim/assign/close**, **operator workflow engine**, **notifications** side effects, **full** admin SPA, **publication**, **bulk** ops, **hard-delete** tour, **admin order/payment mutations**. Internal **ops** JSON handoff claim/close remains **separate** from admin API. Still **no** **`tour_id` reassignment**, **no** route/itinerary editor.

**Earlier checkpoints:** Phase 6 / Steps 1–7 (foundation through core tour patch); Phase 6 / Steps 8–10 (boarding create / patch / delete); Phase 6 / Steps 11–12 (tour translation upsert/delete); Phase 6 / Steps 13–14 (boarding point translation upsert/delete); Phase 6 / Step 15 (tour archive/unarchive); Phase 6 / Step 16 (order detail payment correction visibility); Phase 6 / Step 17 (order detail action preview); Phase 6 / Step 18 (admin handoff queue read API); Phase 5 accepted + Step 20 docs (`docs/PHASE_5_ACCEPTANCE_SUMMARY.md`).

**Phase 5 (closed for MVP):** Execution checkpoints **Steps 4–19** are summarized in `docs/PHASE_5_ACCEPTANCE_SUMMARY.md` and per-step notes under `docs/PHASE_5_STEP_*_NOTES.md`; **Step 20** was documentation/consolidation only (no intended production-code churn for acceptance).

**Next safe direction:** **Phase 6 / Step 19** — **narrow admin handoff status mutation** (controlled; **not** full workflow engine) — see **Next Safe Step** below.

**Optional follow-ups** (not Phase 5 blockers; prioritize with product): Telegram Web App init-data validation for Mini App APIs, real payment provider (PSP), broader handoff/waitlist customer notifications.

`docs/IMPLEMENTATION_PLAN.md` lists phases 1–9; **Step N** labels in **this** file are **project checkpoints** (not substeps inside the plan table).

## Completed Steps

### Phase 1
- Phase 1 / Step 1 completed
  - backend skeleton created
  - config/settings structure added
  - PostgreSQL setup added
  - SQLAlchemy base added
  - Alembic initialized
  - `/health` and `/healthz` added
  - modular folder layout created

- Phase 1 / Step 2 completed
  - `.gitignore` refined
  - `.env.example` refined
  - `README.md` refined with local bootstrap instructions
  - `docs/DEPLOYMENT.md` refined
  - local PostgreSQL bootstrap notes added
  - Alembic local migration workflow documented

### Phase 2
- Phase 2 / Step 1 completed
  - first core ORM models added
  - initial meaningful Alembic migration added
  - tables added:
    - users
    - tours
    - tour_translations
    - boarding_points
    - orders

- Phase 2 / Step 2 completed
  - supporting ORM models added
  - second Alembic migration added
  - tables added:
    - payments
    - waitlist
    - handoffs
    - messages
    - content_items
    - knowledge_base

- Phase 2 / Step 3 completed
  - repository layer added
  - Pydantic schemas added
  - repositories kept data-oriented
  - schemas kept separate from ORM

- Phase 2 / Step 4 completed
  - first read-oriented services added
  - service layer foundation added for:
    - catalog lookup
    - tour detail retrieval
    - boarding point retrieval
    - user profile read
    - order read
    - payment read
    - knowledge base lookup

- Phase 2 / Step 5 completed
  - safe preparation/read services added
  - services added for:
    - catalog preparation
    - language-aware tour read
    - order summary
    - payment summary

### Phase 2 Test Checkpoint
- enum persistence mismatch fixed
- enum-backed model columns now persist enum values correctly for PostgreSQL
- focused unit test slice added and passed
- repository/read/preparation layers verified by unit tests

### Phase 3
- Phase 3 / Step 1 completed
  - private bot foundation added under `app/bot/`
  - bot startup wiring added
  - private-only handlers added for:
    - `/start`
    - `/language`
    - `/tours`
    - language callbacks
    - simple tour detail browsing
  - safe deep-link style entry added for `tour_<CODE>`
  - multilingual templates/keyboards/minimal FSM state added
  - bot layer kept thin and service-driven
  - no reservation creation
  - no payment flow
  - no waitlist flow
  - no handoff workflow
  - no group behavior
  - no Mini App UI

- Phase 3 / Step 2 completed
  - private chat browsing extended for:
    - date preference via guided presets
    - destination/tour-name keyword
    - budget range when safe within one currency
  - reusable filtering kept in app service layer
  - handlers stayed thin
  - no booking/payment/waitlist/handoff logic added

- Phase 3 / Step 3 completed
  - reservation-preparation slice added
  - flow now supports:
    - selected tour
    - seat count choice
    - boarding point choice
    - multilingual reservation-preparation summary
  - summary clearly marked as preview only
  - no reservation row created yet
  - no seat mutation yet
  - no payment flow yet

- Phase 3 / Step 4 completed
  - first real temporary reservation creation added
  - implemented through app-layer `TemporaryReservationService`
  - private bot now creates a temporary reservation/order from prepared flow
  - minimal write state now includes:
    - `booking_status=reserved`
    - `payment_status=awaiting_payment`
    - `cancellation_status=active`
    - `reservation_expires_at`
  - available seats are reduced at reservation time
  - multilingual temporary reservation confirmation added
  - still postponed:
    - payment session creation
    - payment reconciliation
    - waitlist actions
    - handoff workflow
    - reminder workers
    - expiry worker execution
    - group behavior
    - Mini App UI

### Phase 4
- Phase 4 / Step 1 completed
  - first payment-entry slice added
  - implemented through `PaymentEntryService`
  - private bot now supports continue-to-payment for an existing temporary reservation
  - validates that:
    - order belongs to the user
    - order is still `reserved`
    - order is still `awaiting_payment`
    - order is not canceled
    - order has not expired
  - creates a minimal payment session/payment record tied to the order
  - reuses latest pending payment session instead of creating duplicates
  - payment step response now shows:
    - reservation reference
    - payment session reference
    - amount due
    - reservation expiry
  - uses a minimal mock/provider-agnostic payment-entry foundation
  - nothing is marked as paid yet

- Phase 4 / Step 2 completed
  - payment reconciliation slice added
  - implemented through `app/services/payment_reconciliation.py`
  - reconciliation now consumes a verified, provider-agnostic payment result payload
  - matching payment and linked order are locked during reconciliation
  - optional amount/currency validation is applied
  - confirmed payment now:
    - sets payment status to `paid`
    - updates order `payment_status` to `paid`
    - confirms a still-active reserved order
  - duplicate paid results are idempotent and harmless
  - later non-paid results do not regress an already paid order
  - supporting schema contracts added in `app/schemas/payment.py`:
    - `PaymentProviderResult`
    - `PaymentReconciliationRead`
  - repository support added for locked lookup by `(provider, external_payment_id)`

- Phase 4 / Step 3 completed
  - minimal payment webhook/API delivery slice added
  - `POST /payments/webhooks/{provider}` added in `app/api/routes/payments.py`
  - isolated webhook parsing/verification helper added in `app/api/payment_webhook.py`
  - HMAC signature verification via `X-Payment-Signature`
  - provider-agnostic payload parsing and status normalization into `PaymentProviderResult`
  - `PaymentWebhookPayload` and `PaymentWebhookResponse` added to `app/schemas/payment.py`
  - `PAYMENT_WEBHOOK_SECRET` added to config
  - payments router wired into `app/api/router.py`
  - route layer stays thin: verify, parse, delegate, respond
  - `PaymentReconciliationService` remains the only place that mutates payment/order state

- Phase 4 / Step 4 completed
  - first reservation expiry automation slice added
  - implemented through `app/services/reservation_expiry.py`
  - thin worker entry added in `app/workers/reservation_expiry.py`
  - eligible expired temporary reservations now:
    - keep `booking_status=reserved`
    - set `payment_status=unpaid`
    - set `cancellation_status=cancelled_no_payment`
    - clear `reservation_expires_at`
  - seats are restored safely to the related tour
  - expiry behavior is idempotent and PostgreSQL-first

- Phase 4 / Step 5 completed
  - notification preparation foundation added
  - implemented through `app/services/notification_preparation.py`
  - multilingual notification payload preparation added for:
    - temporary reservation created
    - payment pending
    - payment confirmed
    - reservation expired
  - safe event selection uses existing lifecycle states only
  - language fallback stays explicit and service-layer driven

- Phase 4 / Step 6 completed
  - notification dispatch/envelope foundation added
  - implemented through `app/services/notification_dispatch.py`
  - dispatch preparation now wraps prepared notification payloads into a channel-specific envelope
  - minimal dispatch key generation added for de-duplication-friendly preparation
  - current channel support is limited to `telegram_private`
  - no real sending or scheduler/orchestrator complexity added yet

- Phase 4 / Step 7 completed
  - first payment-pending reminder worker slice added
  - implemented through `app/services/payment_pending_reminder.py`
  - thin worker entry added in `app/workers/payment_pending_reminder.py`
  - due reminder selection now covers active temporary reservations that are approaching expiry
  - current reminder window is the first narrow slice only:
    - payment pending shortly before reservation expiry
  - reminder preparation reuses existing notification dispatch groundwork
  - repeated execution stays safe because this slice does not mutate order/payment state or perform real delivery yet

- Phase 4 / Step 8 completed
  - first real `telegram_private` notification delivery slice added
  - implemented through `app/services/notification_delivery.py`
  - minimal delivery adapter/service boundary added for prepared dispatches
  - payment-pending reminder delivery slice added on top of the existing reminder groundwork
  - delivery result handling stays explicit and testable

- Phase 4 / Step 9 completed
  - notification outbox / persistence groundwork added
  - notification outbox model, repository, and service added
  - deterministic dispatch-key dedupe now persists pending notification entries safely
  - payment-pending reminder outbox slice added for enqueueing due reminder dispatches

- Phase 4 / Step 10 completed
  - notification outbox processing slice added
  - implemented through `app/services/notification_outbox_processing.py`
  - pending outbox entries can be picked up in narrow batches for processing
  - processing reuses the existing delivery service and marks entries delivered or failed explicitly

- Phase 4 / Step 11 completed
  - notification outbox recovery groundwork added
  - implemented through `app/services/notification_outbox_recovery.py`
  - failed and stale-processing outbox entries can be safely recovered to `pending`
  - repeated recovery execution stays explicit and repeat-safe

- Phase 4 / Step 12 completed
  - notification outbox retry execution slice added
  - implemented through `app/services/notification_outbox_retry_execution.py`
  - recovered or targeted pending outbox entries can be reprocessed through the existing processing path
  - retry execution remains narrow and does not add scheduler/orchestrator complexity

- Phase 4 / Step 13 completed
  - predeparture reminder groundwork added
  - implemented through `app/services/predeparture_reminder.py` and `app/services/predeparture_reminder_outbox.py`
  - `predeparture_reminder` event support added to notification preparation
  - eligible confirmed, paid, active orders departing within the reminder window can now be prepared and enqueued for `telegram_private`
  - repeated prepare/enqueue execution stays dedupe-friendly and state-safe

- Phase 4 / Step 14 completed
  - departure-day reminder groundwork added
  - implemented through `app/services/departure_day_reminder.py` and `app/services/departure_day_reminder_outbox.py`
  - `departure_day_reminder` event support added to notification preparation
  - eligible confirmed, paid, active same-day departure orders can now be prepared and enqueued for `telegram_private`
  - repeated prepare/enqueue execution stays dedupe-friendly and state-safe

- Phase 4 / Step 15 completed
  - post-trip reminder groundwork added
  - implemented through `app/services/post_trip_reminder.py` and `app/services/post_trip_reminder_outbox.py`
  - `post_trip_reminder` event support added to notification preparation
  - eligible confirmed, paid, active returned trips within the reminder window can now be prepared and enqueued for `telegram_private`
  - repeated prepare/enqueue execution stays dedupe-friendly and state-safe

### Phase 5
- Phase 5 / Step 1 completed
  - Mini App UX definition added in `docs/MINI_APP_UX.md`
  - screen map, CTA hierarchy, loading/empty/error states, timer states, and postponed behaviors documented
  - Mini App UX aligned with current Phase 2-4 service capabilities and postponed scope

- Phase 5 / Step 2 completed
  - first Mini App implementation slice added for foundation + catalog + filters
  - minimal Mini App catalog endpoint added at `GET /mini-app/catalog`
  - Mini App read-only catalog/filter service added in `app/services/mini_app_catalog.py`
  - Flet Mini App foundation added under `mini_app/`
  - scope kept narrow:
    - no reservation UI
    - no payment UI
    - no waitlist flow
    - no handoff/operator workflow
    - no Mini App auth/init expansion

- Phase 5 / Step 3 completed
  - read-only Mini App tour detail screen added
  - catalog cards now navigate to a dedicated tour detail view
  - minimal read-only tour detail endpoint added at `GET /mini-app/tours/{tour_code}`
  - Mini App read-only detail service added in `app/services/mini_app_tour_detail.py`
  - detail screen reuses existing localization and boarding-point read capabilities
  - scope kept narrow:
    - no reservation UI
    - no payment UI
    - no waitlist flow
    - no handoff/operator workflow
    - no Mini App auth/init expansion

- Phase 5 / Step 4 completed
  - commit: `a9342cc` — `feat: add mini app reservation preparation ui`
  - Mini App reservation **preparation** UI (seat count, boarding point, preparation-only summary)
  - preparation endpoints: `GET /mini-app/tours/{tour_code}/preparation`, `GET /mini-app/tours/{tour_code}/preparation-summary`
  - service: `app/services/mini_app_reservation_preparation.py`
  - scope kept narrow:
    - preparation-only — **no** real reservation/order creation in this step
    - no payment UI
    - no waitlist flow
    - no handoff/operator workflow
    - no Mini App auth/init expansion

- Phase 5 / Step 5 completed
  - commit: `929988f` — `feat: add mini app reservation creation and payment start`
  - real Mini App temporary reservation creation added
  - implemented through thin Mini App glue on top of existing service-layer foundations
  - Mini App now supports:
    - real temporary reservation creation from preparation flow
    - reservation success screen with:
      - reservation reference
      - amount to pay
      - payment status
      - reservation expiry / timer-friendly text
    - payment start / continue-to-payment from Mini App
    - payment screen with:
      - amount due
      - reservation deadline
      - payment session reference
      - provider-neutral `Pay Now` flow
  - added Mini App reservation overview glue for user-facing reservation/payment state display
  - business rules remain owned by existing backend services:
    - `TemporaryReservationService`
    - `PaymentEntryService`
  - payment reconciliation remains unchanged and is still the only source of truth for paid-state transition
  - scope kept narrow:
    - no waitlist workflow
    - no handoff/operator workflow
    - no Mini App auth/init expansion
    - no my bookings screen
    - no provider-specific payment integration
    - no admin/group/content changes

### Phase 5 / Step 5 manual local validation
- local backend startup passed
- `/health` returned 200
- `/healthz` returned 200
- Mini App manual flow passed locally using a temporary local test tour:
  - catalog
  - tour detail
  - reservation preparation
  - preparation summary
  - confirm reservation
  - reservation success state
  - reservation overview
  - payment entry
  - payment screen
- current payment screen remains honest/provider-neutral and does not mark anything as paid before backend reconciliation

- Phase 5 / Step 6 completed
  - commit: `<PUT_COMMIT_HASH_HERE>` — `feat: add mini app bookings and booking status view`
  - Mini App My Bookings screen added
  - Mini App Booking Detail / Status View added
  - thin Mini App facade layer added for user-facing booking/payment state translation
  - added:
    - `GET /mini-app/bookings`
    - `GET /mini-app/orders/{id}/booking-status`
  - Flet Mini App now supports:
    - bookings list
    - booking detail / status view
    - state-based CTA:
      - `Pay now`
      - `Browse tours`
      - `Back to bookings`
  - current facade behavior includes:
    - active temporary hold -> `Pay now`
    - expired hold before worker cleanup -> `Browse tours`
    - released hold after worker cleanup -> human-readable released/expired state + `Browse tours`
    - confirmed/paid booking -> `Back to bookings`
  - payment summary is reused through existing read/summary services
  - payment reconciliation remains unchanged and is still the only source of truth for paid-state transition
  - scope kept narrow:
    - no waitlist workflow
    - no handoff/operator workflow
    - no Mini App auth/init expansion
    - no provider-specific checkout
    - no refund flow
    - no admin/group/content changes

### Phase 5 / Step 6 test checkpoint
- tests run:
  - `python -m unittest tests.unit.test_api_mini_app tests.unit.test_services_mini_app_booking_facade tests.unit.test_services_mini_app_booking -v`
- result:
  - all listed tests passed

- Phase 5 / Step 7 completed
  - commit: `<PUT_COMMIT_HASH_HERE>` — `feat: add mini app help placeholder and language settings`
  - Mini App help placeholder added
  - Mini App language/settings screens added
  - added:
    - `GET /mini-app/help`
    - `GET /mini-app/settings`
    - `POST /mini-app/language-preference`
  - Flet Mini App now supports:
    - `/help`
    - `/settings`
    - help/settings entry points from high-friction screens
    - server-backed language hydration after startup
    - language preference update through the existing user context path
  - current help behavior stays honest:
    - support/help information is available
    - real operator handoff from Mini App is still not implemented
  - language preference is persisted through existing Telegram user context service behavior
  - scope kept narrow:
    - no waitlist workflow
    - no real handoff/operator workflow
    - no Mini App auth/init expansion
    - no provider-specific checkout
    - no refund flow
    - no admin/group/content changes

### Phase 5 / Step 7 test checkpoint
- tests run:
  - `python -m unittest tests.unit.test_api_mini_app -v`
- result:
  - all listed tests passed

### Phase 5 — extended execution (Steps 8–20, historical)

These steps are **closed** for the Phase 5 MVP acceptance narrative; detail lives in `docs/PHASE_5_ACCEPTANCE_SUMMARY.md` and `docs/PHASE_5_STEP_*_NOTES.md`. This subsection records **durable facts** and a **compact map** (not a live “next step” checklist).

**Staging / ops facts (still relevant):**
- Typical hosted layout: **API backend** + **Telegram bot (webhook)** + **Mini App UI** as separate processes/services; **PostgreSQL** is the staging DB; `TEST_BELGRADE_001` is a staging-oriented test tour.
- **Data hygiene:** accumulated staging holds/orders can make a tour look sold out; `reset_test_belgrade_tour_state.py` resets the test tour and related artifacts when needed before smoke tests.
- **Lazy expiry** (Step 9): expiry can run without relying on a dedicated cron for several paths; configurable override **`TEMP_RESERVATION_TTL_MINUTES`** (defaults preserve the 6h/24h rule family documented elsewhere).
- **Mock payment completion** (Step 10): `ENABLE_MOCK_PAYMENT_COMPLETION` + `POST /mini-app/orders/{id}/mock-payment-complete` funnels through the same **`PaymentReconciliationService`** path as webhooks.
- **Expired hold DB shape** (admin/read-model caution): expired unpaid holds may combine **`booking_status=reserved`** with **`payment_status=unpaid`**, **`cancellation_status=cancelled_no_payment`**, **`reservation_expires_at=null`** — see `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` for interpretation risk.

**Compact step map (pointers):**
- **Step 8–8C:** private chat ↔ Mini App staging alignment; scroll/shell i18n iterations; smoke checklist — see early step notes / commit history.
- **Step 9–9A:** lazy expiry + configurable TTL — notes above.
- **Step 10:** mock payment completion — `docs/PHASE_5_STEP_10_NOTES.md`.
- **Step 11:** My bookings sections — `docs/PHASE_5_STEP_11_NOTES.md`.
- **Step 12:** booking detail + payment UX hardening — `docs/PHASE_5_STEP_12_NOTES.md`.
- **Step 12A / 12B:** private chat message cleanup + `/start` `/tours` edit/replace behavior — `docs/PHASE_5_STEP_12A_NOTES.md`, `docs/PHASE_5_STEP_12B_NOTES.md`.
- **Step 13:** support/handoff entry — `docs/PHASE_5_STEP_13_NOTES.md`.
- **Step 14:** waitlist interest entry — `docs/PHASE_5_STEP_14_NOTES.md`.
- **Step 15–17:** internal ops JSON queues + claim/close — `docs/PHASE_5_STEP_15_NOTES.md` … `docs/PHASE_5_STEP_17_NOTES.md`.
- **Step 18:** waitlist status visibility — `docs/PHASE_5_STEP_18_NOTES.md`.
- **Step 19:** My bookings history compaction — `docs/PHASE_5_STEP_19_NOTES.md`.
- **Step 20:** documentation-only acceptance/consolidation — `docs/PHASE_5_ACCEPTANCE_SUMMARY.md`.

**Still not done (product/ops; not Phase 5 MVP acceptance blockers):** real PSP integration, richer mock failure/cancel paths, production Telegram Web App init-data validation for Mini App APIs, full operator inbox/notifications — track via `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`.

### Phase 6
- Phase 6 / Step 1 completed
  - **Config:** `ADMIN_API_TOKEN` in `app/core/config.py`; documented in `.env.example`
  - **Auth dependency:** `app/api/admin_auth.py` — `require_admin_api_token` (Bearer or `X-Admin-Token`; same ergonomics as ops queue)
  - **Routes:** `app/api/routes/admin.py` — `GET /admin/overview`, `GET /admin/tours`, `GET /admin/orders` (lists; wired in `app/api/router.py`)
  - **Read-side:** `app/services/admin_read.py`, `app/services/admin_order_lifecycle.py` — orders expose **`lifecycle_kind`** / **`lifecycle_summary`** instead of relying on raw enums alone for ambiguous expired holds
  - **Repositories:** `TourRepository.list_by_departure_desc`, `OrderRepository.list_recent_for_admin` (read-only lists)
  - **Tests:** `tests/unit/test_api_admin.py`, `tests/unit/test_services_admin_order_lifecycle.py`
  - **Scope respected:** no public Mini App / bot / customer API behavior changes; no booking/payment/waitlist/handoff workflow changes
  - **Historical prompt:** `docs/CURSOR_PROMPT_PHASE_6_STEP_1.md`

- Phase 6 / Step 2 completed
  - **Route:** `GET /admin/orders/{order_id}` — read-only **order detail** (`AdminOrderDetailRead` in `app/schemas/admin.py`)
  - **Includes:** tour + boarding point summaries, capped payment rows, linked handoff summaries, **`persistence_snapshot`** for raw enums while **`lifecycle_*`** stays primary
  - **Repository:** `OrderRepository.get_by_id_for_admin_detail`; payments via `PaymentRepository.list_by_order`
  - **Tests:** extended `tests/unit/test_api_admin.py` (detail, 404, auth, expired-hold projection)
  - **Scope respected:** public flows unchanged; no mutations
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_2.md` (historical); use **Next Safe Step** for new work

- Phase 6 / Step 3 completed
  - **Route:** `GET /admin/tours/{tour_id}` — read-only **tour detail** (`AdminTourDetailRead`, `AdminTranslationSummaryItem` in `app/schemas/admin.py`)
  - **Includes:** core tour fields, translation snippets (language + title), boarding point summaries, **`orders_count`** (row count for visibility only)
  - **Repository:** `TourRepository.get_by_id_for_admin_detail` (eager-load translations + boarding points)
  - **Tests:** extended `tests/unit/test_api_admin.py` (tour detail, 404, auth, translations/boarding/`orders_count`)
  - **Scope respected:** public flows unchanged; no CRUD / mutations
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_3.md` (historical)

- Phase 6 / Step 4 completed
  - **Read-only list filtering:** optional query parameters on **`GET /admin/tours`** and **`GET /admin/orders`** (no mutations)
  - **`GET /admin/tours`:** `status`, `guaranteed_only`
  - **`GET /admin/orders`:** `lifecycle_kind`, `tour_id` — **`lifecycle_kind`** filtering stays **service-driven** and consistent with **`describe_order_admin_lifecycle`** / **`sql_predicate_for_lifecycle_kind`**
  - **Repositories:** `TourRepository.list_by_departure_desc`, `OrderRepository.list_recent_for_admin` (filter args)
  - **Tests:** extended `tests/unit/test_api_admin.py` (filtered lists + auth; unfiltered defaults unchanged)
  - **Scope respected:** public flows unchanged; no CRUD
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_4.md` (historical)

- Phase 6 / Step 5 completed
  - **Route:** **`POST /admin/tours`** — **create-only** core **`Tour`** (`AdminTourCreate` → **`AdminTourDetailRead`** in `app/schemas/admin.py`)
  - **Write service:** `app/services/admin_tour_write.py` — **`AdminTourWriteService.create_tour`**; validation (dates, **`sales_deadline`** vs departure, duplicate **`code`**) in **service layer**; **`seats_available`** = **`seats_total`** on create
  - **Repository:** `TourRepository.create` (base repository) for persistence; route **`db.commit()`** after success
  - **Not in this step:** translations/boarding/media/update/delete/archive
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, duplicate **409**, validation **400**)
  - **Scope respected:** public Mini App / bot / customer flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_5.md` (historical)

- Phase 6 / Step 6 completed
  - **Route:** **`PUT /admin/tours/{tour_id}/cover`** — set/replace **one** **`cover_media_reference`** (`AdminTourCoverSet` → **`AdminTourDetailRead`**)
  - **Persistence:** `tours.cover_media_reference` (nullable string); Alembic revision **`20260405_04`**
  - **Write service:** `AdminTourWriteService.set_tour_cover`; **`TourRepository.set_cover_media_reference`**
  - **Explicitly not in this step:** real **upload** subsystem, **gallery**/media library, **public catalog / Mini App** cover delivery changes, **full** tour update/delete/archive
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success + overwrite, 404, blank payload)
  - **Scope respected:** public booking/payment/waitlist/handoff flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_6.md` (historical)

- Phase 6 / Step 7 completed
  - **Route:** **`PATCH /admin/tours/{tour_id}`** — **`AdminTourCoreUpdate`** (partial core fields only; **`extra='forbid'`** for `code` / `cover_media_reference` / unknown keys)
  - **Write service:** `AdminTourWriteService.update_tour_core`; date/`sales_deadline` validation; **conservative `seats_total`** rule (see **`docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`** **section 18**)
  - **Repository:** `TourRepository.update_core_fields`
  - **Explicitly not in this step:** **`code`** mutation, cover via PATCH, **delete/archive**, translations CRUD, boarding CRUD, public catalog/Mini App changes, full tour-management platform
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, 404, validation, seats rule, forbidden extra fields)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_7.md` (historical)

- Phase 6 / Step 8 completed
  - **Route:** **`POST /admin/tours/{tour_id}/boarding-points`** — **`AdminBoardingPointCreate`** → **`AdminTourDetailRead`**
  - **Write service:** `AdminTourWriteService.add_boarding_point`; **Repository:** `BoardingPointRepository.create_for_tour`
  - **Explicitly not in this step:** boarding **update/delete**, **translations**, **`tour_id` reassignment**, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, tour 404, blank fields)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_8.md` (historical)

- Phase 6 / Step 9 completed
  - **Route:** **`PATCH /admin/boarding-points/{boarding_point_id}`** — **`AdminBoardingPointUpdate`** → **`AdminTourDetailRead`**
  - **Write service:** `AdminTourWriteService.update_boarding_point`; **Repository:** `BoardingPointRepository.update_core_fields`
  - **Explicitly not in this step:** boarding **delete**, **translations**, **`tour_id` reassignment**, full route/itinerary, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, 404, validation, empty body, **`tour_id` in body rejected**)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_9.md` (historical)

- Phase 6 / Step 10 completed
  - **Route:** **`DELETE /admin/boarding-points/{boarding_point_id}`** — **204 No Content** when deleted; **409** if orders reference the point
  - **Write service:** `AdminTourWriteService.delete_boarding_point`; **Repositories:** `OrderRepository.count_by_boarding_point`, base **`delete`** on **`BoardingPoint`**
  - **Explicitly not in this step:** batch delete, boarding **translations**, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, 404, order-reference conflict)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_10.md` (historical)

- Phase 6 / Step 11 completed
  - **Route:** **`PUT /admin/tours/{tour_id}/translations/{language_code}`** — **`AdminTourTranslationUpsert`** → **`AdminTourDetailRead`**
  - **Write service:** `AdminTourWriteService.upsert_tour_translation`; **Repository:** `TourTranslationRepository` create + **`update_fields_for_tour_language`**; language allowlist via **`get_settings().telegram_supported_language_codes`**
  - **Explicitly not in this step:** translation **delete**, **boarding** translations, bulk ops, publication workflow, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, create/update, unsupported language, tour 404, empty body, create without title)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_11.md` (historical)

- Phase 6 / Step 12 completed
  - **Route:** **`DELETE /admin/tours/{tour_id}/translations/{language_code}`** — **204 No Content** when deleted
  - **Write service:** `AdminTourWriteService.delete_tour_translation`; **Repository:** delete by tour + language; language allowlist via **`get_settings().telegram_supported_language_codes`**
  - **Explicitly not in this step:** **boarding** translations, bulk ops, publication workflow, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success, tour 404, translation 404, unsupported language, validation)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_12.md` (historical)

- Phase 6 / Step 13 completed
  - **Route:** **`PUT /admin/boarding-points/{boarding_point_id}/translations/{language_code}`** — **`AdminBoardingPointTranslationUpsert`** → **`AdminTourDetailRead`**
  - **Migration:** Alembic **`20260405_05`** — table **`boarding_point_translations`**
  - **Write service:** `AdminTourWriteService.upsert_boarding_point_translation`; **Repository:** boarding point translation create/update; language allowlist via **`get_settings().telegram_supported_language_codes`**
  - **Explicitly not in this step:** boarding translation **delete**, bulk ops, publication workflow, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, create/update, boarding point 404, unsupported language, validation, empty body)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_13.md` (historical)

- Phase 6 / Step 14 completed
  - **Route:** **`DELETE /admin/boarding-points/{boarding_point_id}/translations/{language_code}`** — **204 No Content** when deleted
  - **Write service:** `AdminTourWriteService.delete_boarding_point_translation`; **Repository:** `BoardingPointTranslationRepository.delete_for_boarding_point_language`; language allowlist via **`get_settings().telegram_supported_language_codes`**
  - **Explicitly not in this step:** bulk ops, publication workflow, public catalog/Mini App changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, success removes one language only, boarding point 404, translation 404, unsupported language)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_14.md` (historical)

- Phase 6 / Step 15 completed
  - **Routes:** **`POST /admin/tours/{tour_id}/archive`**, **`POST /admin/tours/{tour_id}/unarchive`** → **`AdminTourDetailRead`**
  - **Write service:** `AdminTourWriteService.archive_tour`, `unarchive_tour`; **`sales_closed`** reused as archived bucket; unarchive → **`open_for_sale`**; **no** schema migration
  - **Explicitly not in this step:** hard delete, full status editor, order/payment mutations, publication, public catalog logic changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, archive success, archive idempotent, unsafe status, unarchive success, unarchive idempotent, unarchive rejects non-archived, 404)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_15.md` (historical)

- Phase 6 / Step 16 completed
  - **Endpoint:** **`GET /admin/orders/{order_id}`** — extended **`AdminOrderDetailRead`** with **`payment_correction_hint`**, **`needs_manual_review`**, **`payment_records_count`**, **`latest_payment_status`**, **`latest_payment_provider`**, **`latest_payment_created_at`**, **`has_multiple_payment_entries`**, **`has_paid_entry`**, **`has_awaiting_payment_entry`**
  - **Service:** `compute_payment_correction_visibility` in **`app/services/admin_order_payment_visibility.py`**; **`AdminReadService.get_order_detail`** loads all payment rows once for count + capped list
  - **Explicitly not in this step:** order/payment **mutations**, reconciliation **changes**, webhooks, public API changes
  - **Tests:** `tests/unit/test_api_admin.py` (existing detail + multiple payments + mismatch cases)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_16.md` (historical)

- Phase 6 / Step 17 completed
  - **Endpoint:** **`GET /admin/orders/{order_id}`** — extended **`AdminOrderDetailRead`** with **`suggested_admin_action`**, **`allowed_admin_actions`**, **`payment_action_preview`** (advisory only)
  - **Service:** `compute_admin_action_preview` in **`app/services/admin_order_action_preview.py`**; uses **`lifecycle_kind`**, Step 16 **correction** visibility, and **open handoff** count
  - **Explicitly not in this step:** order/payment **mutations**, new mutating routes, webhooks, public API changes
  - **Tests:** `tests/unit/test_api_admin.py` (detail + manual_review / handoff / clean / active-hold cases)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_17.md` (historical)

- Phase 6 / Step 18 completed
  - **Routes:** **`GET /admin/handoffs`**, **`GET /admin/handoffs/{handoff_id}`** → **`AdminHandoffListRead`** / **`AdminHandoffRead`**
  - **Repository:** `HandoffRepository.list_for_admin`, `get_by_id_for_admin_detail`; **service:** `compute_handoff_queue_fields`, **`AdminReadService.list_handoffs`**, **`get_handoff_detail`**
  - **Read fields:** **`is_open`**, **`needs_attention`**, **`age_bucket`**, plus status, reason, priority, user/order/tour linkage, timestamps
  - **Explicitly not in this step:** admin handoff **mutations**, claim/assign/close, notifications, public/catalog changes
  - **Tests:** `tests/unit/test_api_admin.py` (auth, list, filter, detail, 404)
  - **Scope respected:** public flows unchanged
  - **Prompt archive:** `docs/CURSOR_PROMPT_PHASE_6_STEP_18.md` (historical)

---

## Verified

### Environment / Runtime
- `.venv` created and active
- Python 3.13.x is used in project venv
- local PostgreSQL is installed and running
- app starts successfully with `uvicorn`

### Health / Startup
- `/health` returns OK
- `/healthz` returns OK

### Migrations
- Alembic migrations work
- `alembic current` / `heads` checked
- `alembic downgrade -1` and `upgrade head` passed for both migration slices

### Code Sanity
- `python -m compileall app alembic` passed repeatedly after major steps
- `python -m compileall app tests` passed at latest checkpoints
- no major startup/import/mapping crashes at latest checkpoint

### Tests
- focused Phase 2 unit slice passes
- bot foundation tests pass
- reservation service tests pass
- reservation expiry tests pass
- payment entry tests pass
- payment reconciliation tests pass
- API payment tests pass
- notification preparation tests pass
- notification dispatch tests pass
- notification delivery tests pass
- payment-pending reminder worker tests pass
- payment-pending reminder delivery tests pass
- notification outbox tests pass
- payment-pending reminder outbox tests pass
- notification outbox processing tests pass
- notification outbox recovery tests pass
- notification outbox retry execution tests pass
- predeparture reminder tests pass
- predeparture reminder outbox tests pass
- departure-day reminder tests pass
- departure-day reminder outbox tests pass
- post-trip reminder tests pass
- post-trip reminder outbox tests pass
- `python -m unittest discover -s tests/unit -v` currently passes
- re-run and refresh this line after major phases; last intentional full-unit note was kept current through Phase 5 MVP acceptance work
- previous `psycopg ResourceWarning` no longer appears in full suite output

### Latest Payment/Webhook Checkpoint
- payment webhook/API delivery slice passes tests
- route layer remains thin
- reconciliation logic remains isolated in service layer
- app startup after webhook slice passed
- `/health` and `/healthz` both returned 200 after latest changes

### Latest Expiry/Notification Checkpoint
- reservation expiry slice passes tests
- notification preparation slice passes tests
- notification dispatch slice passes tests
- `telegram_private` notification delivery slice passes tests
- payment-pending reminder selection, delivery, and outbox slices pass tests
- notification outbox persistence, processing, recovery, and retry execution slices pass tests
- predeparture reminder groundwork and outbox slices pass tests
- departure-day reminder groundwork and outbox slices pass tests
- post-trip reminder groundwork and outbox slices pass tests
- notification preparation, dispatch, delivery, outbox, and reminder logic remain service-layer driven
- current real notification delivery remains limited to `telegram_private`

---

## Current Architecture State

### Ready
- **bot layer** — Telegram private chat; thin handlers; service-driven
- **api layer** — FastAPI; public routes + Mini App routes + payments webhooks + **internal ops** JSON endpoints + **admin API** (`/admin/*`, `ADMIN_API_TOKEN`: overview, tours/orders **lists** with **optional read-only filters**, **`GET /admin/handoffs`** and **`GET /admin/handoffs/{handoff_id}`** handoff queue visibility, **`GET /admin/orders/{order_id}`** order detail with **Step 16** correction + **Step 17** action-preview fields, **tour + order detail** incl. **`cover_media_reference`**, **`POST /admin/tours`** create **core** tours, **`POST /admin/tours/{tour_id}/archive`** and **`POST /admin/tours/{tour_id}/unarchive`**, **`PUT /admin/tours/{tour_id}/cover`** for **one** media reference string, **`PATCH /admin/tours/{tour_id}`** for **core** field updates only, **`POST` / `PATCH` / `DELETE`** boarding points, **`PUT` / `DELETE`** **`/admin/tours/{tour_id}/translations/{language_code}`** for **tour** translations, **`PUT` / `DELETE`** **`/admin/boarding-points/{boarding_point_id}/translations/{language_code}`** for **boarding** translations)
- **services layer** — business rules and orchestration
- **repositories layer** — persistence-oriented data access
- **mini_app** — Flet Mini App UI (separate deploy surface in staging); **MVP accepted** for agreed scope (`docs/PHASE_5_ACCEPTANCE_SUMMARY.md`); **no business logic in the frontend** — UI calls APIs only
- **booking/payment core** — temporary reservations, payment entry, idempotent reconciliation, lazy expiry, staging mock payment completion path when enabled
- **waitlist / handoff (MVP)** — interest entry, support request, read-only ops visibility + narrow claim/close actions; not a full operator inbox or customer notification suite

### Architecture boundaries (non-negotiable)
- **PostgreSQL-first** for MVP-critical behavior; do not treat SQLite as source of truth for booking/payment paths
- **Service layer** owns business logic; **repositories** stay persistence-oriented; **route layer** stays thin (verify/parse/delegate)
- **Payment reconciliation** remains the single place for confirmed paid-state transitions on orders
- **Mini App / any web UI**: presentation only — no duplicated booking/payment rules in the client

### Not Implemented Yet
- **Phase 6 / Step 19 (next):** first narrow **admin handoff status mutation** slice (e.g. claim/close or equivalent **controlled** transitions under **`/admin/*`** — exact verbs TBD; **not** a full workflow engine)
- **Later (explicit schedule):** **admin order/payment mutations** only with product approval and **without** bypassing **`payment reconciliation`**; translation **bulk**, **publication**, media **upload/delivery**, tour **hard-delete**, **full** admin SPA — per **`docs/IMPLEMENTATION_PLAN.md`**
- **Phase 7–9:** group assistant, handoff at scale, content assistant, analytics — per `docs/IMPLEMENTATION_PLAN.md`

## Next Safe Step

**Phase 6 / Step 19 — first narrow admin handoff status mutation slice.**

### Goal
After Step 18 **read-only** queue visibility, add the **smallest** **ADMIN_API_TOKEN**-gated way to change **handoff operational state** (e.g. align with existing **`open` / `in_review` / `closed`** conventions) **without** building an inbox product, **without** customer notification side effects in this step, and **without** duplicating internal **ops** JSON unless deliberately unified.

### Safe scope
- **One** or **two** narrow **PATCH**/**POST** routes under **`/admin/handoffs/...`** — exact design in implementation; **service-layer** validation; **no** public routes

### Not in this step
- Payment/order **mutations**, refund/capture, reconciliation rewrite, webhooks, publication, **full** SPA, notification **delivery** engine

### Must not expand without a dedicated step
- **Bulk** tour/translation ops, **publication**, **public** booking contract changes, arbitrary **operator** RBAC beyond token scope

**Completed step references:** `docs/CURSOR_PROMPT_PHASE_6_STEP_1.md` … `docs/CURSOR_PROMPT_PHASE_6_STEP_18.md` (historical).  
**Plan:** `docs/IMPLEMENTATION_PLAN.md` (Phase 6)

## Recommended Next Prompt
Implement **Phase 6 / Step 19** (**narrow admin handoff status mutation**) using `docs/CHAT_HANDOFF.md` (**Next Safe Step**), `docs/IMPLEMENTATION_PLAN.md`, `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, `docs/TECH_SPEC_TOURS_BOT.md`, and `docs/TESTING_STRATEGY.md`. Add `docs/CURSOR_PROMPT_PHASE_6_STEP_19.md` when starting — **do not** use Phase 5 “next step” prompts for new work.

---

## Important Technical Notes

- PostgreSQL is the primary target database
- do not treat SQLite as source of truth for booking/payment-critical behavior
- repository layer must stay persistence-oriented only
- service layer must stay separate from repositories
- handlers must stay thin and service-driven
- enum persistence was already fixed and must not be broken again
- current bot foundation uses `MemoryStorage()` as an early-stage temporary choice
- bot process and backend process should remain separable
- temporary reservation creation already reduces `seats_available`, so later payment and expiry logic must respect this existing write behavior
- payment reconciliation is already idempotent and must remain the single place for confirmed payment state transitions
- webhook/API route layer must remain thin and must not duplicate reconciliation logic
- DB-backed test harness now disposes the engine pool centrally after class teardown
- see `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md` for accepted temporary decisions, open architectural questions, and future review triggers

---

## Current Bot Layer Notes

### Existing bot capabilities
- private `/start`
- explicit language selection
- language resolution/persistence for Telegram users
- `/tours`
- safe list of open tours
- safe tour detail browsing
- `/start tour_<CODE>` style deep-link handling
- guided browsing by:
  - date presets
  - destination keyword
  - budget range when safe
- reservation-preparation preview flow
- temporary reservation creation confirmation
- continue-to-payment entry for temporary reservations

### Bot constraints
- **waitlist:** interest entry exists for sold-out open tours (MVP); no group-chat waitlist UX
- **handoff:** support/contact entry exists; full operator inbox and customer notifications are **not** implemented
- **group chat:** not in scope for current MVP slices

### Mini App (Phase 5 MVP — accepted)
- End-to-end staging-realistic flow: catalog → detail → preparation → **temporary reservation** → **payment entry** → optional **mock completion** → **My bookings** (with documented limits); see `docs/PHASE_5_ACCEPTANCE_SUMMARY.md`
- Production **Telegram Web App init-data** validation for API identity remains a **follow-up**, not a blocker for this handoff narrative

---

## Reservation Expiration Assumption Currently Implemented

- departure in 1–3 days: 6 hours
- departure in 4+ days: 24 hours
- always capped by `sales_deadline` if earlier

This logic already exists in the temporary reservation creation slice and must be preserved unless deliberately revised.

---

## Payment Logic Status Currently Implemented

### Already implemented
- payment entry
- minimal payment session creation/reuse
- idempotent payment reconciliation
- paid result can confirm the order
- later non-paid result cannot regress a paid order
- webhook/API delivery slice with isolated signature verification and payload parsing
- provider-agnostic reconciliation entry via `POST /payments/webhooks/{provider}`

### Not yet implemented
- refund workflow
- advanced provider SDK integration
- admin-facing payment operations beyond current core flow

---

## Notification Logic Status Currently Implemented

### Already implemented
- multilingual notification preparation for:
  - temporary reservation created
  - payment pending
  - payment confirmed
  - reservation expired
- multilingual notification preparation for:
  - predeparture reminder
  - departure-day reminder
  - post-trip reminder
- notification event/type definitions
- channel-specific dispatch envelope preparation for `telegram_private`
- real `telegram_private` notification delivery
- deterministic dispatch key generation for prepared dispatches

### Not yet implemented
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications

---

## New Chat Startup Prompt

Start this task as a continuation of the current project state, but in a fresh chat.

Use the following as source of truth for continuity:
- project rules
- current codebase
- docs/TECH_SPEC_TOURS_BOT.md
- docs/IMPLEMENTATION_PLAN.md
- docs/CHAT_HANDOFF.md (latest approved checkpoint and **Next Safe Step**)
- docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- docs/TESTING_STRATEGY.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md

Continuity rules:
- preserve the existing architecture and phase sequence
- do not repeat already completed work
- do not reintroduce previously postponed logic
- continue from the last approved checkpoint in `docs/CHAT_HANDOFF.md` (**Phase 6 / Step 18** complete; forward work: **Phase 6 / Step 19** per **Next Safe Step**)

Forward **Phase 6** work only — do not use legacy Phase 5 “next step” prompts for new implementation slices.
