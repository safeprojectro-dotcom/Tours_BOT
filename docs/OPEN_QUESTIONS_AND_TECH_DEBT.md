# Open Questions and Tech Debt

## Purpose
Track temporary decisions, accepted shortcuts, open architectural questions, and future review points for Tours_BOT.

This file is for items that are acceptable **now**, but should not be forgotten later.

---

## 1. Reservation expiry status semantics

### Current decision
After reservation expiry:
- `booking_status` remains `reserved`
- `payment_status` becomes `unpaid`
- `cancellation_status` becomes `cancelled_no_payment`
- `reservation_expires_at` becomes `None`

### Why accepted now
- keeps the expiry implementation minimal
- preserves idempotent worker behavior
- prevents double seat restoration
- avoids introducing a new booking terminal status too early

### Risk later
- admin views may interpret expired reservations as still reserved
- customer booking history may become confusing
- analytics and status-based filtering may become ambiguous
- future workflow code may incorrectly rely on `booking_status` alone

### Revisit trigger
- before admin order/status screens are finalized
- before analytics/reporting logic is finalized
- before production release if status-based filtering becomes ambiguous

### Status
open

---

## 1a. Admin read API vs raw reservation/order semantics

### Current decision
- **Phase 6 / Step 1** admin **list** endpoints (`GET /admin/orders`, etc.) expose orders with **`lifecycle_kind`** / **`lifecycle_summary`** (see `app/services/admin_order_lifecycle.py`) so operators are less likely to misread **expired unpaid holds** as active reservations when scanning lists.
- **Phase 6 / Step 16** extends **`GET /admin/orders/{order_id}`** with **read-only** **payment correction visibility** fields (hints, counts, latest payment metadata; see `app/services/admin_order_payment_visibility.py`). **`lifecycle_kind` / `lifecycle_summary`** remain **primary**; hints are **secondary** and conservative from persisted order + payment rows only. Step 16 is **intentionally** non-mutating; **refunds**, forced **paid-state** edits, and manual **reconciliation** commands stay **postponed** until product defines safety rules and an explicit slice.
- **Phase 6 / Step 17** adds **read-only** **action preview** fields on the same endpoint (**`suggested_admin_action`**, **`allowed_admin_actions`**, **`payment_action_preview`**; see `app/services/admin_order_action_preview.py`). These are **advisory** only and do **not** execute or authorize mutations; **payment**-row admin **mutations** (refund/capture/cancel-payment) remain **postponed** until explicit product approval (**Phase 6 / Steps 23–26** are narrow **order** mutations and do **not** write payment rows; **Steps 27–28** are read-side only — lifecycle alignment + move-readiness hints; **Step 29** is a narrow **order** move mutation and does **not** write payment rows).
- **Phase 6 / Step 18** adds **`GET /admin/handoffs`** and **`GET /admin/handoffs/{handoff_id}`** for **read-only** handoff **queue** visibility (**`is_open`**, **`needs_attention`**, **`age_bucket`**, plus persisted fields).
- **Phase 6 / Step 19** adds **`POST /admin/handoffs/{handoff_id}/mark-in-review`** (`open`→`in_review`, idempotent `in_review`, `closed` rejected). **Phase 6 / Step 20** adds **`POST /admin/handoffs/{handoff_id}/close`** (`in_review`→`closed`, idempotent `closed`, `open` rejected; unexpected statuses rejected narrowly). Admin **`close`** intentionally **depends** on moving **`open` → `in_review`** first — not a shortcut from **`open`**. **Phase 6 / Step 21** adds **`POST /admin/handoffs/{handoff_id}/assign`** (narrow **`assigned_operator_id`** on **`open`/`in_review`** only; **reassign** to another operator rejected once set — see `docs/CHAT_HANDOFF.md`). **Phase 6 / Step 22** adds **`POST /admin/handoffs/{handoff_id}/reopen`** (`closed`→`open`, idempotent `open`, `in_review` rejected; **`assigned_operator_id` preserved** on reopen). Handoff **admin** surface remains **intentionally narrow** (no general state machine). **Unassign**, broader **reassignment** policy, and full operator **workflow** remain **postponed**. Internal **ops** JSON remains a **separate** surface from **`/admin/*`**.
- **Phase 6 / Step 23** adds **`POST /admin/orders/{order_id}/mark-cancelled-by-operator`**: **operator cancellation** for **active temporary holds** only (aligned with admin “active hold” lifecycle); **paid** orders and other disallowed state combinations are **rejected**; **no** payment-row mutation, **no** refund/reconciliation change.
- **Phase 6 / Step 24** adds **`POST /admin/orders/{order_id}/mark-duplicate`**: **duplicate** marking for **active temporary hold** or **expired unpaid hold** only; **paid** orders **rejected**; **no** merge, **no** payment-row mutation.
- **Phase 6 / Step 25** adds **`POST /admin/orders/{order_id}/mark-no-show`**: **confirmed + paid + active cancellation** only, **`tour.departure_datetime` in the past** (UTC); terminal **`no_show`/`no_show`**; **no** seat restoration, **no** payment-row mutation.
- **Phase 6 / Step 26** adds **`POST /admin/orders/{order_id}/mark-ready-for-departure`**: **confirmed + paid + active cancellation** only, **`tour.departure_datetime` strictly in the future** (UTC); **`booking_status` → `ready_for_departure` only**; **no** seat mutation, **no** payment-row mutation.
- **Phase 6 / Step 27** (read-only): **`AdminOrderLifecycleKind.READY_FOR_DEPARTURE_PAID`** in **`app/services/admin_order_lifecycle.py`** so **`ready_for_departure` + paid + active** maps to a **first-class** admin lifecycle label (not generic **`other`**); **`sql_predicate_for_lifecycle_kind`** and **`GET /admin/orders?lifecycle_kind=`** stay consistent; **`admin_order_action_preview`** treats this kind like **confirmed paid** for preview noise.
- **Phase 6 / Step 28** (read-only): **`GET /admin/orders/{order_id}`** adds **`can_consider_move`**, **`move_blockers`**, **`move_readiness_hint`** (**`app/services/admin_order_move_readiness.py`**) — conservative decision-support for operators; **does not** perform a move by itself.
- **Phase 6 / Step 29** (narrow mutation): **`POST /admin/orders/{order_id}/move`** (**`app/services/admin_order_move_write.py`**) — move when Step **28**-style readiness passes; **no** payment-row writes, **no** reconciliation semantics change.
- **Phase 6 / Step 30** (read-only): **`GET /admin/orders/{order_id}`** adds **`move_placement_snapshot`** (**`app/services/admin_order_move_inspection.py`**) — **current** tour/boarding placement for inspection only; **`timeline_available`** is **false** because **no** persisted move audit/timeline rows exist yet. **Closure:** **`docs/PHASE_6_REVIEW.md`** — narrow Phase 6 track **closed**; default forward path **transition**, **not** payment admin. **Payment**-row admin **mutations** (refund/capture/cancel-payment) remain **postponed** (see **§1f** below).
- **Database fields are unchanged:** the combination described in **section 1** (`booking_status` may remain `reserved` after expiry, etc.) still exists at persistence layer.

### Why core debt remains open
- Raw status **semantics** in section 1 are still the source of truth for storage and workers; projection only helps **read** surfaces that use it.
- **Admin mutations**, **reporting**, **analytics**, or dashboards that filter on raw enums **without** the same projection rules can still misinterpret state.

### Revisit trigger
- before **admin mutation** flows (status changes, cancellations, manual fixes)
- before **richer admin reporting** or exports that aggregate by raw status
- before **analytics / dashboards** depend directly on raw status combinations without a documented projection layer

### Status
open (read-side **partially mitigated** for Phase 6 Step 1 list API, Steps 16–17 order-detail hints/preview, Step 18 handoff queue reads, Steps **19–22** narrow handoff mutations, Steps **23–26** narrow order mutations, Step **27** **`ready_for_departure_paid`** lifecycle read refinement, Step **28** move-readiness hints, Step **29** narrow move **mutation**, Step **30** **`move_placement_snapshot`** (current placement only); **section 1** remains open for semantics and non-projected consumers; **persisted** move timeline/audit and broader admin order workflow **postponed** — see **`docs/CHAT_HANDOFF.md` Next Safe Step**)

---

## 1b. Admin tour core create vs cover / media attachment

### Current decision
- **Phase 6 / Step 5** adds **`POST /admin/tours`** for **core** `Tour` fields only — **no** binary upload in that step.
- **Phase 6 / Step 6** adds **`PUT /admin/tours/{tour_id}/cover`** to persist **one** optional **`cover_media_reference`** string (URL or storage key) per tour — **not** a file upload endpoint and **not** a media library.
- **Real** upload subsystem, CDN/object-store integration, and **customer-facing** cover delivery via catalog/Mini App remain **intentionally postponed** until explicitly scheduled (see `docs/CHAT_HANDOFF.md` **Not Implemented Yet** / forward steps).

### Revisit trigger
- before admin **tour management** or **end-to-end media handling** is treated as **MVP-complete**
- before production reliance on **binary upload** or **public** cover URLs without a documented storage/delivery strategy

### Status
open (reference string can be set; **upload/delivery** not done)

---

## 1c. Admin boarding points — narrow create/update/delete vs full lifecycle

### Current decision
- **Phase 6 / Steps 8–10** add **`POST`**, **`PATCH`**, and **`DELETE /admin/boarding-points/{boarding_point_id}`** for core boarding fields; delete is blocked when **orders** reference the point (see implementation).
- **Phase 6 / Steps 13–14** add **per-language** **`PUT` / `DELETE`** under **`/admin/boarding-points/{boarding_point_id}/translations/{language_code}`** (single row per language; allowlist matches **`telegram_supported_language_codes`**).
- **Full route/itinerary** editing, reorder, and **tour-level** archive/hard-delete remain **intentionally postponed** until scheduled (see `docs/CHAT_HANDOFF.md` **Next Safe Step**).

### Revisit trigger
- before admin treats **boarding management** as **complete** without reorder/itinerary workflows
- before **customer-facing** catalog or booking flows need structural changes tied to boarding CRUD beyond current slices

### Status
open (core CRUD + **narrow** per-language translations; **itinerary/reorder** not done)

---

## 1d. Admin translations — per-language upsert/delete vs bulk/publication

### Current decision
- **Tours:** **Phase 6 / Steps 11–12** — **`PUT`** and **`DELETE`** **`/admin/tours/{tour_id}/translations/{language_code}`** (one row per language).
- **Boarding points:** **Phase 6 / Steps 13–14** — **`PUT`** and **`DELETE`** **`/admin/boarding-points/{boarding_point_id}/translations/{language_code}`** (table **`boarding_point_translations`**, migration **`20260405_05`**).
- **Bulk** translation import/export and **publication** workflow remain **intentionally postponed** (see `docs/CHAT_HANDOFF.md` **Not Implemented Yet**).

### Revisit trigger
- before admin treats **multilingual content ops** as **complete** without bulk tooling or publish pipeline
- before **customer-facing** catalog needs structural changes tied to translation CRUD beyond per-language slices

### Status
open (per-language **upsert/delete** done for tours and boarding points; **bulk** / **publication** **not done**)

---

## 1e. Admin tour archive / unarchive — narrow POST endpoints vs full status editor

### Current decision
- **Phase 6 / Step 15** adds **`POST /admin/tours/{tour_id}/archive`** and **`POST /admin/tours/{tour_id}/unarchive`** only (returns **`AdminTourDetailRead`**). **`sales_closed`** is reused as the **admin “archived”** bucket (no new enum member); **unarchive** sets **`open_for_sale`** only. **Archive** allowed from **draft**, **open_for_sale**, **collecting_group**, **guaranteed**; **not** from in-progress / completed / cancelled / postponed (see service). Idempotent **archive** when already **`sales_closed`**; idempotent **unarchive** when already **`open_for_sale`**.
- **Hard delete**, arbitrary **TourStatus** workflow UI, and **public** catalog semantics beyond existing **`OPEN_FOR_SALE`** scopes remain **out of scope** for this slice.

### Revisit trigger
- before admin needs **audit** fields, **batch** archive, or **status** rules that collide with operational **`sales_closed`** meaning
- before **public catalog** or **customer-facing** semantics assume **`sales_closed`** means only “admin archived” (vs operational “sales ended”)

### Status
open (narrow **two-endpoint** slice; **not** a full lifecycle editor)

---

## 1f. Admin payment-side operations vs reconciliation (future)

### Current decision
- **Admin payment mutations** (refund, capture, cancel-payment, forced paid-state edits, manual reconciliation commands) are **intentionally postponed** — no **`/admin/*`** payment-write slice is implied by Phase 6 Steps **1–30**.
- **Payment reconciliation** (service-layer, webhooks) remains the **single source of truth** for **confirmed paid-state transitions** on orders until product defines a different contract — **this boundary stays intact**; admin tooling must **not** silently bypass it.
- **Phase 6 review** is recorded in **`docs/PHASE_6_REVIEW.md`** (checkpoint **Step 30**). **Revisit** admin payment-side operations **only** via a **separate design checkpoint** (product + safety rules + reconciliation contract) — **not** as the default follow-up to Phase 6 closure.
- **Revisit** before: **real PSP-integrated** admin payment tooling, **refund workflow**, **production payment rollout**, **broader** admin-side payment operations.

### Status
open (by design; **not** default next implementation — see **`docs/PHASE_6_REVIEW.md`** and handoff **Next Safe Step**)

---

## 2. Temporary bot FSM storage uses MemoryStorage

### Current decision
The current bot foundation uses `MemoryStorage()` for FSM state.

### Why accepted now
- simplest safe option for early private bot foundation
- good enough for local development and early flow validation
- avoids introducing Redis complexity too early

### Risk later
- state is lost on bot restart
- unsuitable for more serious production traffic
- can break longer or more fragile user flows
- makes horizontal scaling impossible

### Revisit trigger
- before production-like deployment of Telegram bot
- before longer multi-step user flows are added
- before group and handoff flows become more complex

### Status
open

---

## 3. Payment provider is currently mock/provider-agnostic

### Current decision
Payment entry currently creates a minimal payment session/reference using a mock/provider-agnostic flow.

### Why accepted now
- allows payment flow structure to be built safely
- decouples order/payment architecture from a real provider too early
- enables reconciliation design and tests before real gateway integration

### Risk later
- real provider fields may not match current assumptions
- webhook payloads, status mapping, and error handling may need expansion
- payment entry UX may need revision after real provider adoption

### Revisit trigger
- before real provider SDK/API integration
- before production payment rollout
- before Mini App payment implementation

### Status
open

---

## 4. Payment status enum may become too narrow for real provider lifecycle

### Current decision
The existing `payment_status` enum is reused for both order-level payment status and payment records.

Current values include:
- `unpaid`
- `awaiting_payment`
- `paid`
- `refunded`
- `partial_refund`

### Why accepted now
- keeps the MVP schema simpler
- avoids over-modeling provider lifecycle too early
- sufficient for entry + reconciliation foundation

### Risk later
A real provider may require more detailed payment-record states, such as:
- failed
- pending_webhook
- cancelled
- provider_error
- expired

This may create ambiguity between:
- order payment state
- individual payment record state

### Revisit trigger
- before real payment provider integration
- before refund/failure handling is added
- before admin payment operations are expanded

### Status
open

---

## 5. Local test and app flow rely on PostgreSQL-first discipline, but SQLite is still possible in ad hoc contexts

### Current decision
The project is documented and implemented as PostgreSQL-first.

### Why accepted now
- correct choice for booking/payment-sensitive logic
- migrations and concurrency behavior are being verified against PostgreSQL
- aligns with Railway production target

### Risk later
If someone casually runs parts of the project against SQLite:
- lock behavior may differ
- enum behavior may differ
- transaction semantics may differ
- booking/payment assumptions may be misvalidated

### Revisit trigger
- before onboarding another developer
- before writing more concurrency-sensitive booking logic
- before CI environment is finalized

### Status
open

---

## 6. Bot and backend process separation must be preserved

### Current decision
The project keeps bot process and backend process conceptually separate.

### Why accepted now
- cleaner architecture
- prevents Telegram concerns from leaking into backend runtime
- aligns with worker/process model planned in implementation plan

### Risk later
- quick shortcuts may accidentally couple bot startup with API startup
- deployment shortcuts may collapse concerns into one process
- debugging and scaling will become harder

### Revisit trigger
- before production/staging process deployment is finalized
- before workers and reminders are introduced more broadly
- before Railway process layout is finalized

### Status
open

---

## 7. Deep-link tour browsing currently uses safe `tour_<CODE>` convention only

### Current decision
Private bot deep-link entry currently supports the safe pattern:
- `/start tour_<CODE>`

### Why accepted now
- simple and controlled
- easy to validate
- enough for current browsing/detail entry flow

### Risk later
- marketing/source attribution may need richer deep-link payloads
- campaign/channel tracking may need structured parameters
- language or source tags may need preservation

### Revisit trigger
- before marketing campaign deep links are introduced
- before source-channel analytics becomes important
- before Mini App/deep-link routing is expanded

### Status
open

---

## 8. Language handling currently uses simple normalized short codes

### Current decision
Language resolution currently:
- normalizes code
- lowers case
- converts `_` to `-`
- uses the short code before `-`
- accepts only supported languages

### Why accepted now
- simple
- safe
- sufficient for current private flow and early multilingual behavior

### Risk later
- region-specific variants may matter
- content fallback rules may need to become more explicit
- more complex multilingual personalization may outgrow the current simplification

### Revisit trigger
- before multilingual content becomes more complex
- before supporting more localized tour content variants
- before analytics/reporting by language becomes important

### Status
open

---

## 9. Current reservation expiration policy is embedded in service logic

### Current decision
Current implemented expiration assumption:
- departure in 1–3 days -> 6 hours
- departure in 4+ days -> 24 hours
- capped by `sales_deadline` if earlier

### Why accepted now
- enough for the first real reservation workflow
- allows payment-entry and expiry logic to move forward
- aligns with the current MVP-level booking flow

### Risk later
- business may want route-specific or campaign-specific reservation windows
- admin override may be needed
- analytics and payment conversion tuning may require revisiting this policy

### Revisit trigger
- before admin-side booking policy controls are added
- before production tuning of booking/payment conversion
- before route-specific business rules are introduced

### Status
open

---

## 10. Route/API delivery for payment is minimal and mock/provider-agnostic

### Current decision
Webhook/API delivery is intentionally minimal:
- thin route
- isolated verification/parsing helper
- provider-agnostic input mapping into reconciliation service

### Why accepted now
- keeps reconciliation logic clean
- avoids locking into provider SDK too early
- makes testing easier

### Risk later
- real provider SDK/webhook format may require more specific handling
- signature verification may become provider-specific
- retries, duplicates, and provider error semantics may need more nuance

### Revisit trigger
- before real provider integration
- before production payment rollout
- before multiple providers are supported

### Status
open

---

## 11. Seat restoration and seat decrement logic should remain tightly controlled

### Current decision
Seats are:
- decremented at temporary reservation creation
- restored by the expiry worker for eligible unpaid reservations

### Why accepted now
- creates a coherent temporary reservation lifecycle
- matches current write workflow
- supports payment-entry and expiry slices

### Risk later
- future waitlist logic will need to coordinate with restored seats
- handoff/admin manual operations could accidentally conflict
- duplicate restoration risks can reappear if state semantics become inconsistent

### Revisit trigger
- before waitlist release logic
- before admin manual reservation/order interventions
- before analytics around occupancy/load are finalized

### Status
open

---

## 12. Current test harness is now clean, but DB-backed test lifecycle remains important infrastructure

### Current decision
DB-backed unit test harness now centralizes engine disposal after class teardown.

### Why accepted now
- removed the `psycopg ResourceWarning`
- keeps test output clean
- avoids touching production code

### Risk later
- future tests may reintroduce resource leaks
- async or more complex DB usage may need a stronger shared test infrastructure
- test fixture complexity may grow with API/bot/worker layers

### Revisit trigger
- before adding broader API integration tests
- before worker integration tests
- before CI test matrix becomes larger

### Status
open

---

## 13. Repositories intentionally avoid workflow logic

### Current decision
Repositories are persistence-oriented only.

### Why accepted now
- keeps architecture clean
- prevents business logic from leaking into data access layer
- makes services the proper orchestration boundary

### Risk later
- rushed feature work may tempt adding workflow shortcuts into repositories
- duplicated business rules may appear if service boundaries weaken

### Revisit trigger
- on every major workflow addition
- especially booking, payment, waitlist, and handoff slices

### Status
open

---

## 14. Payment reconciliation service is the single source of truth for paid-state transitions

### Current decision
Payment reconciliation service is the only place that should confirm payment and update payment/order state.

### Why accepted now
- preserves idempotency
- avoids state mutation duplication
- creates a clean boundary between route delivery and business logic

### Risk later
- admin tools, provider integration, or bot shortcuts may attempt to bypass reconciliation service
- inconsistent order/payment state may appear if multiple paths can mark payment as paid

### Revisit trigger
- before admin-side payment operations
- before provider-specific payment integrations
- before refund workflow is introduced

### Status
open

---

## 15. Notification/reminder/worker layer is not yet implemented

### Current decision
Workers currently cover reservation expiry only.
Reminder/notification infrastructure is still postponed.

### Why accepted now
- keeps current scope focused
- avoids mixing booking/payment core with notification complexity too early

### Risk later
- delayed implementation may require refactoring order lifecycle triggers
- notification semantics may depend on status assumptions already made

### Revisit trigger
- next Phase 4 worker/reminder slice
- before production rollout of booking/payment flow

### Status
open

---

## 16. Phase 5 Mini App MVP closure — residual debt (non-blocking)

**Added:** Phase 5 / Step 20 consolidation. Phase 5 is **accepted** per `docs/PHASE_5_ACCEPTANCE_SUMMARY.md`. The items below are **not** reopened as blockers; they stay on the backlog for later phases.

| Topic | Where tracked |
|-------|----------------|
| Production Telegram Web App init-data / Mini App API auth | This summary + acceptance doc; replaces dev `MINI_APP_DEV_TELEGRAM_USER_ID` when prioritized |
| Real payment provider (mock/staging paths today) | Section 3 |
| Bot `MemoryStorage` | Section 2 |
| Expiry/booking status semantics for admin/analytics | Section 1 |
| Waitlist auto-promotion and customer notifications | Product / later phase |
| Handoff operator inbox and customer notifications | Phase 6–7 scope |
| Full shell i18n for all languages | Phase 5 used en/ro priority + English fallback |

Do **not** duplicate long analysis here — keep single source of truth in numbered sections above and in `docs/PHASE_5_ACCEPTANCE_SUMMARY.md`.

### Status
open (informational snapshot)

---

## 17. Production schema vs deployed code (Railway / Alembic operational risk)

### Current decision / current lesson
- **Production schema may lag behind deployed code** when Alembic migrations are **not** applied before or alongside a release that already uses new ORM columns. Example (resolved): Phase 6 / Step 6 added `tours.cover_media_reference` in code while production Postgres had not yet run the migration → `sqlalchemy.exc.ProgrammingError` / `psycopg.errors.UndefinedColumn`, breaking any path that loads `Tour` (e.g. **`/mini-app/catalog`**, **`/mini-app/bookings`**) until the schema matched.
- **`railway shell`** (or shell on the platform) does not by itself fix **local** migration runs: internal DB hostnames such as **`*.railway.internal`** are **not resolvable** from a developer machine, so “run Alembic from my laptop against prod” typically requires the **public** Railway Postgres URL (or another supported access path).

### Why accepted now
- Release automation may not yet run **`alembic upgrade head`** on every deploy.
- Teams often validate app code first and treat DB migration as a follow-up — acceptable only until a repeatable release gate exists.

### Risk later
- Repeat **500**s on catalog, bookings, or admin routes after any deploy that ships ORM/model changes without matching DDL.
- Incidents look like “Mini App bugs” but are **pure schema drift**.

### Revisit trigger
- **Before** the next schema-changing deploy (new column/table/enum).
- Before a **release checklist** is considered complete without an explicit **migration + smoke** step.
- Before **production rollout automation** is treated as stable without DB migration in the path.

### Recovery path (documented pattern; not a substitute for automation)
- Confirm drift: e.g. `alembic current` vs `heads` against the target DB.
- Apply migrations using a **reachable** DB URL (often Railway **public** Postgres URL) and a driver-explicit SQLAlchemy URL such as **`postgresql+psycopg://...`** for local Alembic.
- **Redeploy** the backend service after migration; smoke **`/health`**, **`/mini-app/catalog`**, **`/mini-app/bookings`** (and any other routes touching changed models).

### Status
open

---

## 18. Admin `PATCH` `seats_total` vs order-level occupancy

### Current decision
- **Phase 6 / Step 7** — **PATCH /admin/tours/{tour_id}** — may update **`seats_total`** using a **conservative** rule: treat **committed seats** as `seats_total - seats_available`, require any new total **≥** that value, and set **`seats_available`** to `new_total - committed_seats`. This keeps ORM/check constraints coherent **without** summing live **`orders.seats_count`**.
- **Richer validation** (reconcile **`seats_total`** with actual reservations/orders, or block edits when orders exist) remains **postponed** until explicitly scheduled.

### Why accepted now
- Avoids unsafe automatic seat math and keeps the admin slice narrow.
- Order-accurate occupancy rules belong with booking domain work, not a minimal PATCH slice.

### Risk later
- Admin could theoretically set totals that are **inconsistent** with sum of order rows if historical data drifted — unlikely if **`seats_available`** was maintained by existing booking flows.

### Revisit trigger
- before admin tools are used to **reshape** capacity on tours with **many** active bookings
- before **analytics** or **ops** rely on **`seats_*`** alone without order-level checks

### Status
open (narrow rule shipped; **order-sum validation** not implemented)

---

## 19. Phase 7 group runtime vs rules documentation (Step 1 vs Step 2+)

### Current decision
- **Phase 7 / Step 1** delivered **`docs/GROUP_ASSISTANT_RULES.md`** — operational rules only (no code).
- **Phase 7 / Step 2** added **helper-layer** (**group trigger** + **handoff trigger** evaluation): `app/services/group_trigger_evaluation.py`, `handoff_trigger_evaluation.py`, `assistant_trigger_evaluation.py`; tests `tests/unit/test_group_assistant_triggers.py`.
- **Phase 7 / Step 3** added **minimal** **Telegram** **group** runtime: `app/bot/handlers/group_gating.py` + `app/services/group_chat_gating.py` — **group/supergroup text**; **non-trigger** silence; trigger → **one** short ack; **`TELEGRAM_BOT_USERNAME`** unset → silence.
- **Phase 7 / Step 4** wires **`evaluate_handoff_triggers`** in the **same** narrow path **after** **`evaluate_group_trigger`** succeeds — **reply shaping only** (handoff **categories** drive short safe lines in **`app/services/group_chat_gating.py`**); **no** handoff DB rows, **no** operator assignment, **no** workflow engine. Tests: **`tests/unit/test_group_chat_gating.py`** (category cases + non-trigger silence).
- **Forward (documented):** **`docs/CHAT_HANDOFF.md` Next Safe Step** — **Phase 7 / Step 5** = **private CTA / deep-link routing foundation for group replies** (implementation **not** implied by this section until coded).
- **Still postponed** until explicit future slices: **real handoff persistence** from group runtime, **operator workflow engine**, **full** group assistant; optional later: **i18n** acks, **rate limits**, **structured logging** — product-scoped.

### Status
open (Step **4** runtime reply-shaping **shipped**; persistence / operator workflow / full assistant **not** done — see **`docs/CHAT_HANDOFF.md` Next Safe Step**)