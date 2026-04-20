# Open Questions and Tech Debt

## Purpose
Track temporary decisions, accepted shortcuts, open architectural questions, and future review points for Tours_BOT.

This file is for items that are acceptable **now**, but should not be forgotten later.

---

## Checkpoint Sync — UVXWA1 (2026-04-19)

Documentation synchronization checkpoint after completion of Tracks **5g.4a–5g.4e**, **5g.5**, **5g.5b**, **U1/U2/U3**, **V1–V4**, **W1–W3**, **X1/X2**, **A1**, plus key hotfixes and production fixes.

### Resolved and accepted (not open questions)
- **Mode 2 catalog whole-bus line** (5g.4a–5g.4e, 5g.5, 5g.5b) is implemented and accepted for current scope.
- **Mode 3 customer, ops/admin read-side, messaging, supplier clarity** blocks (U/V/W/X) are implemented and accepted.
- **A1 admin operational UI surface** is implemented as additive read-only internal UX over existing admin custom-request APIs.
- **Hotfixes accepted:** supplier-offer `/start` payload/title; request-detail empty-control crash; production schema drift fix for `custom_request_booking_bridges`; custom request submit success-state; custom request **422** validation visibility.

### Compatibility baseline (must remain true)
- **Layer A** remains booking/payment source of truth.
- **`TemporaryReservationService`** remains the single hold path.
- **`PaymentEntryService`** remains the single payment-start path.
- **UI layers** consume read-side truth and must not duplicate backend business rules.
- **Mode 2** and **Mode 3** remain separate semantics.

### Still genuinely open / postponed
- Existing debt items in this file remain open unless explicitly marked closed in their own sections (payment-provider integration, admin payment mutation design gate, FSM storage hardening, notification expansion, etc.).
- Broader lifecycle/payment/bridge redesign is **postponed** and out of scope for UVXWA1 checkpoint sync.
- Historical prompt files are retained as implementation trail; they are **not** a mass-update active checklist.

### Next safe step pointer
- Continue with a narrow **A2** admin operational usability pass (read-side/UI only), without changing RFQ/bridge/payment/booking semantics.

---

## Checkpoint Sync — Y2.3 + Y2.1a (2026-04-20)

### Resolved and accepted (not open questions)
- Supplier v1 operational loop is now implemented in narrow scope: onboarding gate, supplier offer intake, moderation/publication actions, retract path, supplier read-side list, and supplier Telegram lifecycle notifications.
- Approve and publish are explicitly separate semantics (`approve != publish`); reject reason is supplier-visible.
- Supplier onboarding legal/compliance minimum identity fields are required on the pending-approval path: `legal_entity_type`, `legal_registered_name`, `legal_registration_code`, `permit_license_type`, `permit_license_number`.

### Compatibility baseline (must remain true)
- No Layer A booking/payment semantics change.
- No RFQ/bridge execution semantics change.
- No payment-entry/reconciliation semantics change.
- No Mode 2/Mode 3 merge.

### Explicitly accepted compatibility nuance
- Legacy already-approved suppliers remain operationally compatible.
- Existing approved supplier rows may still have NULL in new legal fields by design.
- Legal completeness guard applies to approving pending suppliers, not retroactive forced migration of all approved suppliers.

### Still open / postponed
- Clean-room live verification for a brand-new supplier completing the full legal-hardened onboarding path in production is still pending.
- Legal document upload/KYC file workflow remains postponed.
- Full compliance audit subsystem remains postponed.
- Supplier analytics/dashboard portal rewrite remains postponed.
- Full supplier org/RBAC redesign remains postponed.

### Next safe step pointer
- Narrow supplier operational visibility / basic stats (read-side only, no PII, no booking/payment controls).

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
- **Phase 7.1 — same class of failure:** code that maps **`Tour.sales_mode`** shipped while Postgres **lacked** **`tours.sales_mode`** (migration **`20260416_06`** not applied) → **`psycopg.errors.UndefinedColumn: column tours.sales_mode does not exist`** on any route or worker that loads **`Tour`**. **Recovery:** apply **`python -m alembic upgrade head`** (reachable DB URL) **before** treating the stack as healthy; **do not** mask with app-only “fixes.” **Release gate:** Phase **7.1** deploys **must** include migration apply — see **`COMMIT_PUSH_DEPLOY.md`** (**Deploy-critical**).
- **V2 Track 2 — analogous class of failure:** application code expects **`suppliers`**, **`supplier_api_credentials`**, **`supplier_offers`**, and related enums (Alembic **`20260417_07`**) while Postgres has not applied that revision → failures on **`/admin/suppliers*`**, **`/supplier-admin/*`**, or ORM loads of **`Supplier*`** models (**not** on core **`Tour`** / Mini App catalog **unless** something incorrectly joins supplier tables). **Gate:** same **`alembic current` == `heads`** rule before deploy; see **`COMMIT_PUSH_DEPLOY.md`** (Track **2** note).
- **V2 Track 3 — analogous class of failure:** code expects extended **`supplier_offer_lifecycle`** values and new **`supplier_offers`** columns (**`20260418_08`**) while DB is still at **`20260417_07`** → ORM/API errors on moderation/publish paths and possibly on **`SupplierOffer`** loads. **Gate:** apply **`20260418_08`** before or with deploy that ships Track **3**; see **`COMMIT_PUSH_DEPLOY.md`** (Track **3** note).
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
- **Phase 7 / Step 5** adds **`app/services/group_private_cta.py`** + **`app/schemas/group_private_cta.py`**: **`https://t.me/<bot>?start=grp_private`** (generic) or **`…grp_followup`** (after handoff-category line); appended to group replies. Tests: **`tests/unit/test_group_private_cta.py`**.
- **Phase 7 / Step 6** adds **narrow private `/start`** handling in **`app/bot/handlers/private_entry.py`**: **`match_group_cta_start_payload`**; **`start_grp_private_intro`** / **`start_grp_followup_intro`** in **`app/bot/messages.py`** (two **distinct** short entry messages; Phase **7** / Steps **16–17** add **`start_grp_followup_resolved_intro`**, **`start_grp_followup_readiness_*`**, via **`group_followup_private_intro_key`** when applicable); then catalog — **no** handoff persistence from **`grp_*`** in Step **6**. Tests: **`test_group_private_cta`** (matcher), **`test_private_start_grp_messages`**.
- **Phase 7 / Step 7** adds **narrow** **`handoffs`** persistence on **`/start grp_followup`** only (**reason** **`group_followup_start`**, dedupe **open** by user+reason; **`grp_private`** — **no** write). **`HandoffEntryService`**, **`HandoffRepository.find_open_by_user_reason`**. Tests: **`test_handoff_entry`**, **`test_group_private_cta`** (payload gate).
- **Phase 7 / Step 8** adds **focused runtime/bot-flow tests** for the private **`grp_followup`** chain — **`tests/unit/test_private_entry_grp_followup_chain.py`** (`handle_start` + **`SessionLocal`** test binding + mocked catalog) — **no** production behavior changes.
- **Phase 7 / Step 9** adds **explicit admin read-side visibility** for **`group_followup_start`**: derived **`is_group_followup`**, **`source_label`** on **`GET /admin/handoffs`**, handoff detail, and order-detail handoff summaries — **read-only**; tests **`test_admin_handoff_group_followup_visibility`**, **`test_api_admin`** (focused cases).
- **Phase 7 / Step 10** adds **`POST /admin/handoffs/{handoff_id}/assign-operator`** — **narrow operator assignment** for **`reason=group_followup_start`** **only** (same rules as Step **21** **`assign`**: open/in_review, operator exists, idempotent same id, **no** reassign); general **`POST .../assign`** **unchanged**; **no** notifications; tests **`test_api_admin`** (focused cases).
- **Phase 7 / Step 11** adds **read-side work-state visibility** for **`group_followup_start`**: derived **`is_assigned_group_followup`**, **`group_followup_work_label`** on **`GET /admin/handoffs`**, handoff detail, and order-detail handoff summaries — **read-only**; tests **`test_admin_handoff_group_followup_visibility`**, **`test_api_admin`** (focused cases).
- **Phase 7 / Step 12** adds **`POST /admin/handoffs/{handoff_id}/mark-in-work`** — **narrow take-in-work** for **assigned** **`group_followup_start`** only (**`open` → `in_review`**, **`in_review`** idempotent; **no** migration); tests **`test_api_admin`** (`mark_in_work` cases).
- **Combined Phase 7 / Steps 13–14** add **`POST /admin/handoffs/{handoff_id}/resolve-group-followup`** — **narrow resolve/close** for **`group_followup_start`** only (**`in_review` → `closed`**, **`closed`** idempotent, **`open`** rejected; **no** replacement for Step **20** general **`close`**) and **read-only** **`group_followup_resolution_label`** on admin handoff reads when that reason is **`closed`**; tests **`test_api_admin`**, **`test_admin_handoff_group_followup_visibility`**.
- **Phase 7 / Step 15** adds **read-only** **`group_followup_queue_state`** on admin handoff **list** / **detail** / order-detail summaries and optional **`GET /admin/handoffs?group_followup_queue=`** filter (**`awaiting_assignment`**, **`assigned_open`**, **`in_work`**, **`resolved`**) — **no** write-path changes; tests **`test_api_admin`**, **`test_admin_handoff_group_followup_visibility`**.
- **Phase 7 / Step 16** adds **narrow private resolved-followup confirmation** on **`/start grp_followup`**: **`HandoffRepository.find_latest_by_user_reason`**, **`HandoffEntryService.should_show_group_followup_resolved_confirmation`**, **`start_grp_followup_resolved_intro`** when **no** **open** **`group_followup_start`** and **latest** row is **`closed`**; Step **7** persist semantics **unchanged**; **no** operator chat, **no** handoff push notifications; tests **`test_handoff_entry`**, **`test_private_entry_grp_followup_chain`**.
- **Phase 7 / Step 17** adds **narrow private followup history/readiness** on repeat **`/start grp_followup`**: **`HandoffEntryService.group_followup_private_intro_key`** → **`start_grp_followup_readiness_pending`** / **`_assigned`** / **`_in_progress`**, **`start_grp_followup_resolved_intro`**, or **`start_grp_followup_intro`**; **read-only**; **no** operator IDs in copy; tests **`test_handoff_entry`**, **`test_private_entry_grp_followup_chain`**.
- **Phase 7 final followup/operator consolidation block** — **safe polish only**: unified short private **`grp_followup`** wording, **`/contact`** / **`/human`** + browse-tours CTAs where applicable, admin **`group_followup_work_label`** / **`group_followup_resolution_label`** aligned to the same **queue/work** state model as private copy; tests include **`test_group_followup_phase7_consolidation`** and updates to existing **`grp_followup`** / admin visibility tests; **no** new persistence, **no** mutation/enum/API shape changes, **no** public booking/payment/waitlist/Mini App changes.
- **Continuity note:** **group** chat path (Steps **3–4**) remains **reply-only** (no DB handoff from group messages); **private** **`grp_followup`** chain persists intent (Step **7**), is **test-covered** (Step **8**), is **operator-visible in admin reads** (Steps **9–11** + Step **15** queue bucket), can be **narrow-assigned** via **`assign-operator`** (Step **10**), **taken in-work** via **`mark-in-work`** (Step **12**) after assignment, **resolved** via **`resolve-group-followup`** (Steps **13–14**), with **read-side triage labels** (Step **11**), **resolved** label (Steps **13–14**), **queue-state** (Step **15**), **private** **resolved** acknowledgment (Step **16**), **private** **readiness** copy for repeat entries (Step **17**), and **consolidation-aligned** wording (private + admin reads). **Phase 7** **implementation + consolidation + review** — **`docs/PHASE_7_REVIEW.md`** — is **closed** for this chain; **two-way operator chat** / **handoff push notifications** remain **postponed**.
- **Forward (documented):** **`docs/CHAT_HANDOFF.md`** — **Phase 7.1** **Steps 1–5** shipped; **Step 6** (direct whole-bus self-service **design gate**) remains the **product** next step where applicable; **separate** from Phase **7** **`group_followup_*`**. **V2 supplier marketplace:** **Track 0**–**3** complete (**Track 3** = moderated publication + showcase — **implementation** + stabilization review); **Track 4** (request marketplace) is the next **implementation** track when scheduled — see **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`**. Optional **later** slices: **i18n** polish, group **rate limits**.
- **Still postponed:** **broad** operator **assignment/claim** redesign, **full** **operator workflow engine**, **full** group assistant; **live** Telegram validation **may** still depend on **Railway** / bot deploy health — **product scope** unchanged. Optional later: **i18n** acks, **rate limits**, **structured logging** — product-scoped.

### Status
closed for Phase **7** narrative (**`docs/PHASE_7_REVIEW.md`**) — Steps **4–17** + **final consolidation** **shipped** (group + private **`grp_*`** + **`grp_followup`** persistence + tests + admin visibility + narrow assign / in-work / resolve + queue/read labels + aligned wording). **Postponed:** **operator chat**, **handoff push notifications**, **full** operator workflow — unchanged. **Related active work:** **Phase 7.1** (**`docs/CHAT_HANDOFF.md`**); **V2** supplier marketplace — **Track 0**–**3** shipped (**Layer B** + moderated publication); **Track 4** next — **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`** (**not** mixed into Phase **7** handoff logic **ad hoc**).

---

## 20. Tour sales mode (`per_seat` / `full_bus`)

### Current decision
- **Tour sales mode** is an active **Phase 7.1** sub-track (**separate** from closed Phase **7** **`group_followup_*`** work).
- The design source is **`docs/TOUR_SALES_MODE_DESIGN.md`**.
- Implementation follows the design rollout order: **(1)** admin/source-of-truth → **(2)** backend policy → **(3)** read-side adaptation → **(4)** operator-assisted full-bus → **(5)** optional direct whole-bus self-service — **not** as ad hoc changes inside booking, Mini App, private bot, or Phase **7** handoff flows without an explicit slice.
- **`tour.sales_mode`** (Postgres + ORM) is the **commercial source of truth**; **`TourSalesModePolicyService`** in **`app/services/tour_sales_mode_policy.py`** is the **single service-layer interpretation** for **`per_seat` / `full_bus`** (read-only **`TourSalesModePolicyRead`**; policy is driven **only** by the enum — **not** by **`seats_total`** / **`seats_available`**). **Steps 3–4** wire **read-side** policy into Mini App and private bot; **Step 5** adds operator-assisted full-bus handoff context — see **`docs/CHAT_HANDOFF.md`** **Completed Steps**.
- **`per_seat` / `full_bus`** remains a **tour-level** product/domain concern, not a UI-only tweak.
- **Operations / schema:** Deploying Phase **7.1** tour code without applying **`alembic/versions/20260416_06_add_tour_sales_mode.py`** causes **`column tours.sales_mode does not exist`** — **not** a product logic bug. **Gate:** **`python -m alembic upgrade head`** on the target DB before or with the release (**`COMMIT_PUSH_DEPLOY.md`**, **§17** here).

### Status
open (**Phase 7.1 / Steps 1–5** shipped — admin field, policy service, Mini App + private bot read-side, operator-assisted full-bus path; **Step 6** optional direct whole-bus self-service — **design gate only** until approved — see **`docs/CHAT_HANDOFF.md` Next Safe Step**)

---

## 21. V2 Track 0 — Core Booking Platform freeze (supplier marketplace prep)

### Current decision
- **Track 0** documents the **frozen Layer A** (Core Booking Platform) so **V2** supplier-marketplace tracks do not break existing booking, payment, Mini App, private bot, Phase **7** handoff baseline, or Phase **7.1** **`sales_mode`** behavior by accident.
- **Source of truth:** **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`** (frozen core, compatibility contracts, must-not-break checklist, baseline smoke, migration/deploy guardrails).
- **Schema drift guardrail:** deploy must not outpace DB migrations (**`tours.cover_media_reference`**, **`tours.sales_mode`** / **`20260416_06`**, **V2 Track 2** **`20260417_07`**, **V2 Track 3** **`20260418_08`**, and any future DDL) — see **`COMMIT_PUSH_DEPLOY.md`** and **§17**.

### Status
closed (documentation/guardrails for Track **0**; **no** supplier marketplace implementation in Track **0**)

---

## 22. V2 Track 1 — Supplier marketplace design acceptance / alignment

### Current decision
- **Track 1** is a **documentation-only** gate: confirm the supplier-admin + request-marketplace **design package** aligns with **`docs/TRACK_0_CORE_BOOKING_PLATFORM_BASELINE.md`** before **Track 2** code.
- **Aligned:** Layers **B/C** are **extensions** on **Layer A**; **no** silent redefinition of booking/payment/reservation semantics; **no** default broadening of **Phase 7** **`grp_followup_*`**; **moderated** supplier publication; **RFQ** domain **separate** from normal order lifecycle until explicit bridge; **direct whole-bus self-service** **not** auto-approved (Phase **7.1** Step **6** / V2 **Track 6**).
- **Record:** **`docs/IMPLEMENTATION_PLAN_V2_SUPPLIER_MARKETPLACE.md`** (Track **1** section) + **`docs/SUPPLIER_ADMIN_AND_REQUEST_MARKETPLACE_DESIGN.md`** §13a.

### Status
closed (documentation acceptance / alignment; **no** application code in Track **1**)

---

## 23. V2 Track 2 — Supplier admin foundation (Layer B) — implementation closure

### Current decision
- **Track 2** adds **only** new persistence and APIs: **`suppliers`**, **`supplier_api_credentials`** (SHA-256 hashed API tokens), **`supplier_offers`** with service composition, payment mode, lifecycle (**`draft`** / **`ready_for_moderation`**), commercial/timing/capacity fields; **`supplier_offers.sales_mode`** uses the **existing** PostgreSQL enum **`tour_sales_mode`** (same values as core **`tours.sales_mode`** — **reuse at DDL level**, not a change to **`tours`**).
- **Central admin** (`ADMIN_API_TOKEN`): additive **`POST /admin/suppliers`** (bootstrap + one-time plaintext token), **`GET /admin/suppliers`**, **`GET /admin/suppliers/{id}`**, **`GET /admin/suppliers/{id}/offers`**, **`GET /admin/supplier-offers/{offer_id}`** — **does not** replace or redefine existing admin tour/order/handoff semantics.
- **Supplier admin:** **`/supplier-admin/offers`** (list/detail/create/update) authenticated by **supplier bearer token** (DB lookup); scoped so a supplier cannot read or mutate another supplier’s offers (**404** on cross-tenant access).
- **Explicitly not in Track 2:** customer catalog/checkout changes, request marketplace, publication/moderation workflow beyond supplier-side **`ready_for_moderation`** flag, direct whole-bus self-service, order lifecycle replacement, payment execution changes, Phase **7** **`grp_followup_*`** expansion.

### Residual debt / forward hooks
- **Credential rotation**, multiple active credentials per supplier policy, and full RBAC are **postponed** (bootstrap path is intentional minimum).
- **Tests:** **`tests/unit/base.py`** gained **`create_supplier`**, **`create_supplier_credential`**, **`create_supplier_offer`** helpers for supplier-focused tests; existing **`create_tour` / `create_order`** behavior **unchanged** — see stabilization review (**`docs/CURSOR_PROMPT_TRACK_2_STABILIZATION_AND_REVIEW_V2.md`**).

### Status
closed for **Track 2** scope (foundation + stabilization review); **Track 3** delivered moderation/publication on top (see **§24**)

---

## 24. V2 Track 3 — Supplier offer publication / moderation — implementation + stabilization

### Current decision
- **Track 3** is **additive** on **Track 2**: extends **`supplier_offer_lifecycle`** (**`approved`**, **`rejected`**, **`published`**), adds **`moderation_rejection_reason`**, **`published_at`**, **`showcase_chat_id`**, **`showcase_message_id`** (**`20260418_08`**). **No** **`tours` / `orders` / `payments`** DDL changes.
- **Moderation enforcement:** **`POST /admin/supplier-offers/{id}/publish`** is **only** under **`ADMIN_API_TOKEN`**; **`SupplierOfferModerationService.publish`** accepts **`approved`** only; **rejected** / **draft** / **ready_for_moderation** cannot publish. **Suppliers** cannot call publish (no route on **`/supplier-admin/*`**) and **`SupplierOfferService`** rejects setting **`approved`**, **`rejected`**, or **`published`** on update; **`approved`**/**`published`** rows are **immutable** via supplier API.
- **Telegram:** channel post via Bot API **`sendMessage`** (HTML) to **`TELEGRAM_OFFER_SHOWCASE_CHANNEL_ID`**; **no** supplier direct-to-channel path in code.
- **CTA:** channel HTML includes bot deep link **`supoffer_<id>`**; private **`/start`** resolves **`published`** offers to intro + existing catalog/Mini App home keyboard (**no** new booking semantics).
- **Stabilization review:** no RFQ, bidding, whole-bus self-service, Mini App route churn, or group-gating redesign observed in Track **3** touchpoints; see **`docs/CURSOR_PROMPT_TRACK_3_STABILIZATION_AND_REVIEW_V2.md`**.

### Residual debt / forward hooks
- **Unpublish**, edit/delete channel messages, and linking showcase offers to core **`Tour`** SKUs remain **postponed**.

### Status
closed for **Track 3** scope (publication layer + stabilization review); **Track 4** closure recorded in **§25**; **Track 5a** in **§26**

---

## 25. V2 Track 4 — Custom request marketplace foundation (Layer C) — implementation + stabilization

### Current decision
- **Track 4** is **additive** Layer **C**: **`custom_marketplace_requests`** (customer context, type, dates, route notes, group size, specials, **`source_channel`**, **`status`**, **`admin_intervention_note`**) + **`supplier_custom_request_responses`** (**`declined`/`proposed`**, optional quote) — Alembic **`20260421_10`**. **No** DDL on **`tours`**, **`orders`**, **`payments`**, or **`supplier_offers`** lifecycle beyond pre-Track-4 state.
- **Separation from orders:** intake and services **do not** create **`Order`** rows, holds, or payment sessions; **no** bridge to booking in this track (explicit future track, e.g. **Track 5**).
- **Supplier visibility:** **open** requests listed to all authenticated suppliers (broadcast MVP); **no** ranking, auction, or automated matching.
- **Admin:** list/detail all statuses; **`PATCH`** for note and/or **`status`** (e.g. **`cancelled`**); responses visible on detail.
- **Layer A touchpoints (intentionally narrow):** additive Mini App **`POST /mini-app/custom-requests`**, optional **`/custom-request`** view from Help, private **`/custom_request`** command + FSM; **`help_command_reply`** text extended — core catalog/reservation/payment routes **unchanged**.
- **User model:** **`User.custom_marketplace_requests`** relationship only (ORM navigation + FK from requests to **`users.id`**); **no** change to order/handoff/waitlist relationships.
- **Bot routing:** **`custom_request`** router is registered before **`private_entry`** so FSM handlers win when state is set; **`private_entry`** still owns default private chat behavior when not in custom-request states — see **`docs/CURSOR_PROMPT_TRACK_4_STABILIZATION_AND_REVIEW_V2.md`**.

### Residual debt / forward hooks
- Request → booking/payment **transition contract**, winner selection, commercial ownership (**Track 5**), smarter supplier routing, notifications, customer-facing response UX.

### Status
closed for **Track 4** scope (foundation + stabilization review); **Track 5a** records commercial selection without orders — see **§26**; broader **Track 5** (RFQ→Layer A bridge) remains **when explicitly scoped**

---

## 26. V2 Track 5a — Commercial resolution selection foundation (Layer C) — stabilization

### Current decision
- **Additive only:** Alembic **`20260422_11`** extends **`custom_marketplace_request_status`** (new values), adds **`commercial_resolution_kind`** enum + nullable columns on **`custom_marketplace_requests`**; **no** DDL on **`orders`**, **`payments`**, **`tours`**, **`supplier_offers`**, or handoff tables.
- **No request→order bridge:** codebase review: **`app/services/custom_marketplace_request_service.py`** and related RFQ routes do **not** import or call reservation/payment/order write services; customer Mini App reads return **status + short summary** only.
- **Selection rules:** **`supplier_selected`** requires **`selected_supplier_response_id`** pointing at a **`proposed`** **`SupplierCustomRequestResponse`** with **`request_id`** equal to the parent request; cross-request IDs rejected with **400**.
- **Admin contract:** terminal commercial statuses (**`supplier_selected`**, **`closed_assisted`**, **`closed_external`**, legacy **`fulfilled`**) are **422** on **`PATCH /admin/custom-requests/{id}`**; use **`POST .../resolution`**. **`open`** / **`cancelled`** / notes remain on **`PATCH`** ( **`open`** and **`cancelled`** clear selection + resolution kind).
- **Supplier mutations:** **`PUT .../response`** allowed only for **`open`** and **`under_review`** — not after **`supplier_selected`** / **`closed_*`** / **`cancelled`**.
- **Customer surface:** list/detail endpoints do **not** expose other suppliers’ quotes — summaries are fixed strings from **`customer_visible_summary()`** (English-only MVP text).

### Residual debt / forward hooks
- **Enum downgrade:** **`downgrade`** drops FK columns and **`commercial_resolution_kind`** type but **cannot** remove **`ALTER TYPE ... ADD VALUE`** entries from **`custom_marketplace_request_status`** (PostgreSQL limitation) — documented in migration file comment; plan environments accordingly.
- **PATCH `under_review`:** **`PATCH`** may set **`under_review`** without the stricter field rules enforced on **`POST .../resolution`** (resolution **`under_review`** rejects `selected_supplier_response_id` / `commercial_resolution_kind`). If product needs a strict state machine, align **`PATCH`** with resolution rules or disallow **`under_review`** on **`PATCH`** in a future narrow slice.
- **Track 5 forward:** RFQ → **`Order`** / reservation / payment integration (**5b.2+**), customer-facing multi-quote UX, notifications — **postponed**; **5b.1** bridge record only — see **§27**.

### Status
closed for **Track 5a** scope (selection + resolution recording + review); **no** Layer A semantic change attributed to this track

---

## 27. V2 Track 5b.1 — RFQ booking bridge record (Layer C) — implementation

### Current decision
- **Additive only:** Alembic **`20260423_12`** — table **`custom_request_booking_bridges`** (`request_id`, `selected_supplier_response_id`, `user_id`, nullable `tour_id`, `bridge_status`, `admin_note`, timestamps); enum **`custom_request_booking_bridge_status`**. **No** DDL on **`orders`** / **`payments`**; **no** calls to **`TemporaryReservationService`** or payment entry from bridge code.
- **Admin-only explicit trigger:** **`POST /admin/custom-requests/{id}/booking-bridge`** (optional `tour_id`, `admin_note`); **`PATCH .../booking-bridge`** narrows to `tour_id` / `admin_note` updates. **Not** a side effect of Track **5a** resolution.
- **Eligibility:** request **`supplier_selected`** or **`closed_assisted`**; **`selected_supplier_response_id`** set; response **`proposed`** and same **`request_id`**. **Active bridge** uniqueness: at most one row in **`pending_validation`**, **`ready`**, **`linked_tour`**, **`customer_notified`** per request — second **`POST` → 409**.
- **Tour link (optional):** if `tour_id` set, Tour must exist, **`open_for_sale`**, future **`departure_datetime`**, **`sales_deadline`** null or future, **`seats_available` ≥ 1** — validation for **future** Layer A execution only; **no** hold.
- **Admin read:** **`GET /admin/custom-requests/{id}`** includes **`booking_bridge`** (latest row for that request).

### Residual debt / forward hooks
- **Track 5b.3+:** payment entry UX from bridge context (reuse existing **`payment-entry`** only); supersede/cancel bridge workflows; handoff integration; optional admin “open booking for customer” — **explicit** slices only.
- **Concurrency (low priority):** duplicate active bridge prevention is enforced in **`CustomRequestBookingBridgeService.create_bridge`** before insert (**409**). A rare double-**POST** race could still insert two rows until a **partial unique index** (one active status per **`request_id`**) is added — only if ops reports issues.

### Stabilization review (Track 5b.1 — closure)
- **Scope creep:** **None found** in **`app/services/custom_request_booking_bridge_service.py`**, **`app/repositories/custom_request_booking_bridge.py`**, **`app/api/routes/admin.py`** (booking-bridge routes), **`app/models/custom_request_booking_bridge.py`**, Alembic **`20260423_12`**: **no** `Order` / hold / payment-session writes; **no** **`TemporaryReservationService`**; **no** auto-**`Tour`** creation; **no** customer bridge routes; **no** auth/handoff/marketplace redesign.
- **Track 5a unchanged:** **`admin_apply_resolution`** (**`custom_marketplace_request_service.py`**) updates request/selection fields only — **does not** call **`CustomRequestBookingBridgeService.create_bridge`** or **`patch_bridge`**.
- **Selected response:** Bridge row stores **`selected_supplier_response_id`** from the validated **`SupplierCustomRequestResponse`** (same **`request_id`**, **`proposed`**); not a free-form id.
- **PATCH safety:** **`AdminCustomRequestBookingBridgePatch`** allows **`tour_id`** / **`admin_note`** only; **no** status transitions to execution states in **5b.1**; **no** checkout side effects.
- **Supplier / customer reads:** **`get_open_for_supplier`** builds detail **without** **`booking_bridge`** (remains **admin-only** inspection in **5b.1**).

### Status
closed for **Track 5b.1** scope (bridge persistence + admin API + tests + stabilization review); explicit customer execution entry — **§28**

---

## 28. V2 Track 5b.2 — RFQ bridge execution entry (preparation + existing hold)

### Current decision
- **No new migration** — orchestration + Mini App routes only.
- **Explicit customer entry:** **`GET /mini-app/custom-requests/{id}/booking-bridge/preparation`**, **`POST /mini-app/custom-requests/{id}/booking-bridge/reservations`** — **not** side effects of **5a** resolution or **5b.1** admin bridge create/patch.
- **Gates:** **`CustomRequestBookingBridgeService.resolve_customer_execution_context`** — active bridge, **`tour_id`** set, request/selection/bridge integrity, owning **`telegram_user_id`**, execution-time tour + **`tour_is_customer_catalog_visible`**.
- **Policy:** **`TourSalesModePolicyService`** before hold; **`full_bus`** / non-self-serve → **200** blocked envelope on preparation **`GET`**; **`400`** **`operator_assistance_required`** on **`POST`** hold — **no** silent whole-bus self-serve.
- **Layer A reuse:** **`MiniAppReservationPreparationService.get_preparation`**, **`MiniAppBookingService.create_temporary_reservation`** — **no** new payment path; **no** payment rows created by this slice.
- **Bridge status:** after successful hold, active bridge → **`customer_notified`** (minimal progression).

### Residual debt / forward hooks
- Customer Mini App UX copy/CTA wiring from RFQ detail to these routes; **`POST .../payment-entry`** after hold using existing order id; **`closed_external`** guardrails if needed on execution routes.

### Stabilization review (Track 5b.2 — closure)
- **Scope creep:** **None found** — **`custom_request_booking_bridge_execution.py`**, **`mini_app.py`** bridge routes, **`custom_request_booking_bridge_service.py`** execution context: **no** **`PaymentEntryService`**, **no** **`start_payment_entry`**, **no** implicit calls from **`admin_apply_resolution`** or **`create_bridge`** / **`patch_bridge`** (verified **`custom_marketplace_request_service`** still only **`read_for_admin_detail`** for bridges).
- **Policy:** **`TourSalesModePolicyService.policy_for_tour`** in **`get_execution_preparation`** and **`create_execution_reservation`** before Layer A prep/hold; **`MiniAppBookingService.create_temporary_reservation`** still enforces policy internally (**defense in depth**).
- **Layer A:** **`TemporaryReservationService`** only via existing **`MiniAppBookingService`**; **no** parallel reservation engine.
- **`full_bus`:** preparation returns **200** blocked envelope; reservation **400** **`operator_assistance_required`** — **no** self-serve hold.
- **Bridge status:** **`customer_notified`** only after **successful** hold (**acceptable** minimal slice); preparation **GET** does **not** mutate bridge.
- **HTTP nuance (deferrable):** unknown **`telegram_user_id`** raises **`BookingBridgeNotFoundError`** → **404** `"User not found."` — slightly coarse vs **`400`** on other RFQ routes; **narrow later** only if clients need distinct **`unknown_user`** vs **`no_bridge`**.

### Status
closed for **Track 5b.2** scope (explicit preparation + hold orchestration + tests + stabilization review); payment initiation from bridge context **postponed** (**5b.3+**). **Execution gate composition** extended in **Track 5b.3a** — see **§29** (**`EffectiveCommercialExecutionPolicyService`** **in addition to** **`TourSalesModePolicyService`**; does not widen self-serve eligibility).

---

## 29. V2 Track 5b.3a — RFQ supplier policy + effective commercial execution resolver

### Intent (scope)
- **Additive DDL only:** **`20260424_13`** on **`supplier_custom_request_responses`** — **no** `orders` / `payments` / `tours` semantic rewrites.
- **Supplier intent at RFQ response row:** declared **`tour_sales_mode`** + **`supplier_offer_payment_mode`** mirror offer-level vocabulary; **conservative** allowed pairs only.
- **Single read-model resolver:** **`EffectiveCommercialExecutionPolicyService.resolve`** — composes Layer A **`TourSalesModePolicyService`**, supplier declaration, request **`closed_external`** / **`commercial_resolution_kind=external_record`** — **for gating reads and bridge execution only**; **does not** create payments or reservations.

### Supplier policy validation (verified)
- **Proposed:** both **`supplier_declared_sales_mode`** and **`supplier_declared_payment_mode`** **required** (**`SupplierCustomRequestResponseUpsert`**); invalid pairs rejected (**`full_bus` + `platform_checkout`**; no other exotic combos).
- **Declined:** declaring either field **rejected** by schema; repository upsert passes **`None`** — **clears** stored policy on decline.
- **Legacy / incomplete rows:** **`proposed`** with **NULL** policy columns → resolver treats as **`supplier_policy_incomplete`** — **blocks** self-serve (does **not** widen vs post-migration suppliers who must resubmit with fields).

### Effective resolver (verified)
- **`self_service_preparation_allowed`** / **`self_service_hold_allowed`** / **`platform_checkout_allowed`** are **True** only when: not external, not incomplete, supplier declared **`per_seat` + `platform_checkout`**, and **`TourSalesModePolicyService`** allows per-seat self-service — **conjunctive** (strict **narrowing** vs tour-only gate when supplier chose assisted/full-bus intent).
- **Assisted supplier intent** (**`assisted_closure`**, **`full_bus` + `assisted_closure`**, etc.): **`supplier_platform_per_seat_intent`** false → self-serve and platform checkout **blocked**.
- **External:** **`closed_external`** or **`external_record`** → **`external_only`**, checkout and self-serve **blocked**.
- **Stability:** deterministic flags + **`blocked_code`** / **`blocked_reason`** / **`customer_blocked_code`**; no random widening paths identified.

### Bridge execution + payment side effects (verified)
- **`CustomRequestBookingBridgeExecutionService`:** calls resolver **before** prep/hold; **`create_temporary_reservation`** unchanged; **no** **`PaymentEntryService`** / payment-session code in execution module.
- **`full_bus` tour:** still blocked via **`tour_sales_mode_blocks_self_service`** (same customer envelope family as before).
- **Per-seat happy path:** unchanged when supplier declares **`per_seat` + `platform_checkout`** and tour allows per-seat self-service.

### Read contracts (verified)
- **Mini App bridge preparation:** **`effective_execution_policy`** added — JSON clients that ignore unknown keys **remain safe**; strict clients must accept new required field on this response type (additive contract on **one** response model).
- **Admin detail:** **`effective_execution_policy`** nullable — present only when **`booking_bridge.tour_id`** and selected response exist; **`SupplierCustomRequestResponseRead`** includes supplier-declared fields for inspection.

### Stabilization review (Track 5b.3a — closure)
- **Scope creep:** **None found** — **no** new payment routes, **no** payment row creation from RFQ policy code paths, **no** quote-comparison UI, **no** portal/auth/handoff redesign (grep/service review: **`custom_request_booking_bridge_execution`**, **`effective_commercial_execution_policy`**, **`custom_marketplace_request_service`**, **`mini_app`** bridge routes).
- **Layer A / Tracks 0–5b.2:** standard catalog booking, private bot booking, supplier publication, **5a** resolution, **5b.1** bridge persistence **unchanged** except **additive** supplier **`PUT`** payload requirement for **new/updated proposed** responses and additive API read fields; **migrate → deploy → smoke** discipline preserved (**`COMMIT_PUSH_DEPLOY.md`**).

### Residual / forward
- **Track 5b.3b** — bridge payment **eligibility** read (**§30**) — **completed**; actual payment session remains **`POST /mini-app/orders/{order_id}/payment-entry`** only.
- **Track 5c** — Mini App RFQ bridge UX (**§31**) — **completed** (Flet wiring only; eligibility → existing payment stack).
- **Forward:** optional thin delegate POST — **not** required when eligibility + existing route suffice; supersede/cancel bridge; **“my requests”** hub.

### Status
**closed** for **Track 5b.3a** scope (policy columns + validation + resolver + bridge integration + tests + stabilization review).

---

## 30. V2 Track 5b.3b — Bridge payment eligibility + existing payment-entry reuse

### Intent
- **Read-only gate:** **`GET /mini-app/custom-requests/{request_id}/booking-bridge/payment-eligibility`** (`telegram_user_id`, **`order_id`** required) — returns **`MiniAppBridgePaymentEligibilityRead`** (`payment_entry_allowed`, `order_id`, `effective_execution_policy`, `blocked_code`, `blocked_reason`).
- **No new payment engine:** eligibility does **not** call **`PaymentEntryService.start_payment_entry`**; **`PaymentEntryService.is_order_valid_for_payment_entry`** (read-only) reuses the same rules as payment entry for order state.
- **Anchor:** explicit **`order_id`** from the bridge hold response — **no** guessing among multiple orders.

### Gate (all must hold for `payment_entry_allowed`)
- Active bridge + **`resolve_customer_execution_context`** integrity (same as **5b.2**).
- **`effective.platform_checkout_allowed`** (**5b.3a** resolver).
- Order exists; **`order.user_id`** = bridge customer; **`order.tour_id`** = **`bridge.tour_id`**.
- **`is_order_valid_for_payment_entry`** (reserved, awaiting payment, active cancellation, reservation not expired).

### Explicit non-goals (verified)
- **No** payment rows from eligibility GET; **no** bridge-authoritative payment lifecycle; **no** implicit payment on bridge create/patch/resolution.
- **No** new provider or payment schema.

### Stabilization review (Track 5b.3b — closure)
- **Scope creep:** **None found** — **`get_payment_eligibility`**, **`mini_app`** eligibility route, **`PaymentEntryService.is_order_valid_for_payment_entry`**: **no** `PaymentRepository.create` from eligibility path; **no** `start_payment_entry` from eligibility; **no** bridge-specific payment POST; **no** auto payment after hold; **no** calls from admin bridge create/patch or **5a** resolution; **no** auth/handoff/RFQ UI redesign.
- **Layer A:** **`start_payment_entry`** unchanged except additive read-only helper sharing **`_is_order_valid_for_payment_entry`**; catalog **`POST .../orders/{id}/payment-entry`**, private bot payment entry, **5b.2**/**5b.3a** unchanged in meaning.
- **Payment gate:** **`platform_checkout_allowed`** first; then **`resolve_customer_execution_context`** (active bridge, **`tour_id`**, selection/bridge sync, owning user, tour execution validation); explicit **`order_id`** query param (**no** order guessing); order user/tour alignment; Layer A validity (expired / wrong status → **`order_not_valid_for_payment`**); assisted/external/incomplete policy → blocked before order checks.
- **Read-only:** Eligibility route **no** `session.commit` in handler; service **no** flushes on bridge for eligibility; **`is_order_valid_for_payment_entry`** uses **`OrderRepository.get`** (no `FOR UPDATE`) — same predicate as **`start_payment_entry`** pre-check (**TOCTOU** between GET eligibility and POST payment-entry acceptable; **`start_payment_entry`** re-validates under lock).
- **Read contract:** New **GET** path only — clients that never call it **unchanged**; blocked responses use stable **`blocked_code`** / **`blocked_reason`** for future Mini App wiring.
- **Tests:** **`test_custom_request_booking_bridge_payment_eligibility_track5b3b`** (allowed path + **`payment-entry`** reuse, no payment rows on GET, assisted block, order_not_found / tour_mismatch / expired); regressions **5b.2**, **5b.3a**, **`PaymentEntryService`** — **pass** (acceptance run).

### Status
**closed** for **Track 5b.3b** scope (eligibility route + service + tests + stabilization review).

---

## 31. V2 Track 5c — RFQ Mini App UX wiring (bridge execution + payment continuation)

### Intent
- **Mini App only:** wire **`/custom-requests/{request_id}/bridge`** to **existing** Track **5b.2** preparation/reservation and Track **5b.3b** payment eligibility — **no** new backend payment or booking semantics.
- **CTA policy:** **`Confirm reservation`** after preview when self-service preparation is allowed; **`Continue to payment`** only when overview shows an **active** hold **and** **`payment_entry_allowed`**; then navigate to the **standard** tour payment route so **`POST /mini-app/orders/{order_id}/payment-entry`** runs unchanged.

### Explicit non-goals (verified in scope)
- **No** second reservation or payment architecture in UI; **no** bypass of **`EffectiveCommercialExecutionPolicyService`** / **`PaymentEntryService`**; **no** **`full_bus`** self-serve enablement.

### Residual / forward
- Customer **multi-quote** comparison UI, bridge **supersede/cancel**, bot deep-link templates — **not** **5c**; **My Requests** hub — **Track 5d** (**§32**).

### Stabilization review (Track 5c — closure)
- **Scope creep:** **None found** — changes are confined to **`mini_app/`** (**`api_client`**, **`app.py`**, **`ui_strings`**, **`rfq_bridge_logic`**, unit test); **no** edits to **`app/services/*`** booking/payment, **no** new FastAPI routes, **no** provider/session model, **no** quote-comparison UI, **no** bridge lifecycle/admin/auth/handoff redesign (repo grep + file review).
- **Backend/API consumption:** **`MiniAppApiClient`** calls only **existing** **`GET/POST /mini-app/custom-requests/{id}/booking-bridge/preparation|reservations`**, **`GET .../payment-eligibility`**, plus **already-used** catalog helpers **`GET .../tours/{code}/preparation-summary`** and **`GET .../orders/{id}/reservation-overview`** — same shapes as Track **5b.2** / **5b.3b** / catalog; **no** client-side contract widening (no extra query/body fields beyond server-defined **`MiniAppCreateReservationRequest`** and eligibility params).
- **UI branches:** **`self_service_available`** false → blocked envelope only (**no** seat/boarding, **no** reserve/pay CTAs); true + **`preparation`** → mirrors catalog **`per_seat_self_service_allowed`** gate (assisted copy, **no** confirm row when not per-seat); confirm appears only after successful **preview** (summary block); post-hold **`Continue to payment`** enabled only when **`rfq_bridge_continue_to_payment_allowed`** (active hold **and** **`payment_entry_allowed`**); hold active + pay blocked shows **`blocked_reason`** or safe fallback copy; expired/unknown overview uses existing hold messaging patterns.
- **Payment reuse:** **`RfqBridgeExecutionScreen`** receives **`on_continue_to_payment=self.open_payment_entry`** → **`page.go(/tours/{tour_code}/prepare/payment/{order_id})`** → existing view stack loads **`PaymentEntryScreen.load_payment_entry`** → **`POST /mini-app/orders/{order_id}/payment-entry`** only — **no** parallel payment screen or bridge-specific payment POST.
- **Standard flow:** Catalog **`/`**, **`/tours/...`**, **`/prepare`**, reserved/payment stacks, **`/custom-request`** (exact path) unchanged in ordering; bridge route **`/custom-requests/{id}/bridge`** matched only by dedicated regex **after** **`/custom-request`** branch — **no** path collision.
- **Tests:** **`test_mini_app_rfq_bridge_wiring`** (CTA gating); **`test_custom_request_booking_bridge_execution_track5b2`**, **`test_custom_request_booking_bridge_payment_eligibility_track5b3b`**, **`test_api_mini_app`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5c** scope (Flet wiring + CTA gating test + documentation) — **stabilization reviewed**.

---

## 32. V2 Track 5d — Mini App “My Requests” / RFQ status hub

### Intent
- **Mini App only:** **`/my-requests`** list + **`/my-requests/{id}`** detail — consumes **existing** **`GET /mini-app/custom-requests`**, **`GET .../{id}`**, **`GET .../booking-bridge/preparation`**, **`GET /mini-app/bookings`**, and **`GET .../booking-bridge/payment-eligibility`** (when an active temporary hold exists on the bridge **`tour_code`**).
- **Dominant CTA** (detail): **`Continue to payment`** only when eligibility allows; else **`Continue booking`** when **`self_service_available`**; else **`Open booking`** when a **Layer A** row exists for the linked tour (e.g. confirmed); else **no** CTA — **no** new commercial predicates beyond composing existing reads.

### Explicit non-goals
- **No** multi-quote comparison, **no** bridge supersede/cancel, **no** backend RFQ schema changes, **no** new payment/booking execution paths.

### Residual / forward
- Richer admin/customer notifications, bot deep links to **`/my-requests/{id}`**, quote comparison — **not** **5d**.

### Stabilization review (Track 5d — closure)
- **Scope creep:** **None found** — implementation is confined to **`mini_app/`** (**`app.py`**, **`rfq_hub_cta.py`**, **`ui_strings`**, unit test); **no** new **`app/api/*`** routes, **no** service-layer booking/payment changes, **no** quote comparison, bridge supersede/cancel, notifications, auth, or handoff redesign (grep **`app/api`**, **`app/services`**).
- **Backend/API composition:** **`MiniAppApiClient`** unchanged for new endpoints — hub uses existing **`GET /mini-app/custom-requests`**, **`GET /mini-app/custom-requests/{id}`**, **`GET .../booking-bridge/preparation`**, **`GET /mini-app/bookings`**, **`GET .../booking-bridge/payment-eligibility`** (same query/body contracts as Tracks **5b.2** / **5b.3b** / bookings list); **no** client-side contract widening.
- **Routing:** **`/my-requests`** and **`/my-requests/{id}`** are Flet-only paths; **`_extract_my_request_detail_id`** regex does not collide with **`/custom-requests/{id}/bridge`** or **`/custom-request`**; detail stack mirrors **`/bookings/{id}`** pattern (catalog + list + detail views).
- **CTA resolution:** **`resolve_detail_primary_cta`** returns a **single** dominant kind (payment → confirmed/in-trip open booking → continue booking → any matching tour open booking → none); **`MyRequestDetailScreen`** exposes at most one **`FilledButton`** — mutually exclusive by construction.
- **Bridge/payment reuse:** **`Continue booking`** → **`on_open_bridge` → `open_rfq_bridge_booking` → `/custom-requests/{id}/bridge`** (Track **5c**); **`Continue to payment`** → **`on_continue_payment` → `open_payment_entry`** → standard payment stack + **`POST .../payment-entry`**; **`Open booking`** → **`open_booking_detail`** → **`/bookings/{order_id}`** — **no** parallel RFQ payment or hold UI.
- **Accepted limitation (documented):** **`pick_booking_for_bridge_tour`** runs only when **`prep` is not None** (linked **`tour_code`** from bridge). If preparation returns **404**, the hub does **not** infer **`Open booking`** from generic bookings alone — avoids false links between unrelated orders and RFQs; users still have **My bookings**.
- **Tests:** **`test_mini_app_rfq_hub_cta`**; regressions **`test_mini_app_rfq_bridge_wiring`**, **`test_api_mini_app`**, **`test_custom_marketplace_track5a`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5d** scope (Flet hub + **`mini_app/rfq_hub_cta`** + tests + documentation) — **stabilization reviewed**.

**Track 5e follow-on (hub):** **`MyRequestDetailScreen`** now uses **`latest_booking_bridge_tour_code`** from **`GET /mini-app/custom-requests/{id}`** when preparation is unavailable so **`pick_booking_for_bridge_tour`** can still align **Layer A** bookings to the linked tour after a terminal bridge — see **§33**.

---

## 33. V2 Track 5e — Bridge supersede / cancel lifecycle

### Intent
- **Admin-only** transitions: active bridge → **`superseded`** or **`cancelled`** (**`POST .../booking-bridge/close`**); **replace** path (**`POST .../booking-bridge/replace`**) sets active row to **`superseded`** (if any) then **`create_bridge`** in the **same** DB transaction — avoids the **409** window between close and recreate.
- **Orchestration only:** bridge rows remain **non-authoritative** for orders/payments; close/replace **must not** touch **`orders`** / **`payments`** or **`CustomMarketplaceRequest.status`**.
- **Customer fail-closed:** **`resolve_customer_execution_context`** uses **`get_active_for_request`** (terminal statuses excluded); preparation / reservations / payment-eligibility return **404** when no active bridge.

### Explicit non-goals (verified)
- **No** auto-supersede on winner change, **no** `superseded_by_bridge_id`, **no** refund/cancel-order from bridge, **no** new payment/booking **routes** or provider flows, **no** auth/handoff redesign, **no** RFQ request lifecycle redesign.

### Additive read contract
- **`MiniAppCustomRequestCustomerDetailRead`:** **`latest_booking_bridge_status`**, **`latest_booking_bridge_tour_code`** (nullable) — JSON clients that ignore unknown keys remain safe; strict clients must accept new optional fields on this response type. **Track 5f v1** adds **`proposed_response_count`**, **`offers_received_hint`**, **`selected_offer_summary`** — see **§34**. **Track 5g.1** adds **`commercial_mode`** — see **§35**.

### Residual / forward
- Partial unique index (one **active** bridge per **`request_id`**) if ops reports rare double-**POST** races (**§27**); structured closure reason / audit columns — **explicit** slices only.

### Stabilization review (Track 5e — closure)
- **Scope creep:** **None found** — changes are confined to bridge service/admin routes, customer detail enrichment, Mini App hub/bridge copy + **`rfq_hub_cta`**, **`ui_strings`**, **`tests/unit/test_custom_request_booking_bridge_track5e.py`**, **`test_mini_app_rfq_hub_cta`**; **no** order/payment write services invoked from close/replace; **no** **`TemporaryReservationService`** / **`PaymentEntryService`** mutations from bridge lifecycle.
- **Layer A:** holds and payment validity remain enforced by existing Layer A services; bridge close does not expire or cancel reservations; **Continue to payment** on terminal bridge + active hold uses **`order_id`** via existing **`open_payment_entry`** stack (**`POST .../payment-entry`** still authoritative).
- **Tests:** **`test_custom_request_booking_bridge_track5e`** (close, replace, 404 on execution paths, request status + order unchanged); **`test_mini_app_rfq_hub_cta`** (terminal + hold CTA); regressions **`test_custom_request_booking_bridge_execution_track5b2`**, **`test_custom_request_booking_bridge_payment_eligibility_track5b3b`**, **`test_custom_request_booking_bridge_track5b1`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5e** scope (admin close/replace + fail-closed customer bridge endpoints + hub/detail additive fields + tests + documentation) — **stabilization reviewed**.

---

## 34. V2 Track 5f v1 — Customer multi-quote summary / aggregate visibility

### Intent
- **Read-only** customer visibility on **`GET /mini-app/custom-requests/{id}`**: **`proposed_response_count`**, **`offers_received_hint`**, **`selected_offer_summary`** (nullable nested model).
- **Count:** **`proposed`** responses only — **`declined`** excluded (**`SupplierCustomRequestResponseRepository.count_proposed_for_request`**).
- **Hint:** status-aware neutral English strings (**same MVP style** as **`customer_visible_summary`**); not a bidding or choice prompt.
- **Selected snippet:** only when **`selected_supplier_response_id`** is set **and** request status is **`supplier_selected`**, **`closed_assisted`**, **`closed_external`**, or **`fulfilled`** **and** loaded row is **`proposed`** for the **same** **`request_id`** — allowlisted **`quoted_price`**, **`quoted_currency`**, truncated **`supplier_message_excerpt`** (200 chars), **`declared_sales_mode`**, **`declared_payment_mode`** — **no** supplier code/name/id.

### Explicit non-goals (verified)
- **No** customer winner choice, **no** comparison cards, **no** competing supplier UI, **no** new **`POST`** customer routes, **no** bridge/payment/booking execution changes, **no** request lifecycle redesign.

### Mini App
- **`MyRequestDetailScreen._render_body`** only — informational **`Text`** / **`Column`**; **no** changes to **`resolve_detail_primary_cta`** or hub primary button logic.

### Additive read contract
- **`MiniAppCustomRequestCustomerDetailRead`** extended per **§34**; strict JSON clients must accept new fields; ignores-unknown-keys clients remain safe.

### Residual / forward
- **5f v2+:** anonymized multi-card compare, localized **`offers_received_hint`**, list-row offer hints — **explicit** slices only.

### Stabilization review (Track 5f v1 — closure)
- **Scope creep:** **None found** — **`app/repositories/custom_marketplace.py`** (count), **`app/schemas/custom_marketplace.py`**, **`app/services/custom_marketplace_request_service.py`**, **`mini_app/app.py`** (detail body only), **`mini_app/ui_strings.py`**, **`tests/unit/test_custom_marketplace_track5f_v1.py`**; **no** edits to bridge execution, **`PaymentEntryService`**, or hub CTA helpers.
- **5a authority:** snippet is **derived** from admin **`selected_supplier_response_id`** only; **no** alternate actionable offers.
- **Tests:** **`test_custom_marketplace_track5f_v1`**; regressions **`test_custom_marketplace_track5a`**, **`test_mini_app_rfq_hub_cta`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5f v1** scope (aggregate + allowlisted selected snippet + My Requests detail read-only copy + tests + documentation) — **stabilization reviewed**.

---

## 35. V2 Track 5g.1 — Commercial mode classification (read-side only)

### Intent (Track 5g design gate)
- Explicit **presentation-level** distinction between **Mode 1** (**`supplier_route_per_seat`**), **Mode 2** (**`supplier_route_full_bus`** — catalog full-bus, not RFQ by default), and **Mode 3** (**`custom_bus_rental_request`** — Layer C RFQ).
- **Authoritative derivation:** catalog modes from **`Tour.sales_mode`** only; RFQ detail mode is **constant** **`custom_bus_rental_request`** for **`CustomMarketplaceRequest`** customer reads (no hybrid modes in this slice).

### Implementation surface
- **`CustomerCommercialMode`** (`app/models/enums.py`).
- **`commercial_mode_for_catalog_tour_sales_mode`** (`app/services/customer_commercial_mode_read.py`).
- **`MiniAppTourDetailRead.commercial_mode`** (`app/schemas/mini_app.py`; composed in **`MiniAppTourDetailService`**).
- **`MiniAppCustomRequestCustomerDetailRead.commercial_mode`** (`app/schemas/custom_marketplace.py`; set in **`CustomMarketplaceRequestService.get_customer_detail_mini_app`**).

### Explicit non-goals (verified)
- **No** booking/reserve/payment/bridge execution changes; **no** **`EffectiveCommercialExecutionPolicyService`** / **`PaymentEntryService`** behavior change; **no** RFQ resolution or supplier-response rules change; **no** Mini App CTA or bot routing driven by **`commercial_mode`** in this slice; **no** admin workflow; **no** reopening **Track 5f v1** semantics (**`proposed_response_count`**, hints, snippet unchanged in meaning).

### Additive read contract
- New JSON keys on two existing GET responses; clients that ignore unknown keys remain safe; strict clients must accept **`commercial_mode`** (string enum values as above).

### Stabilization review (Track 5g.1 — closure)
- **Scope creep:** **None found** — grep-confined to enums, mapper, **`mini_app`** / **`custom_marketplace`** schemas, **`mini_app_tour_detail`**, **`custom_marketplace_request_service`** (customer detail only), and focused tests; **no** edits to bridge services, payment entry, or order lifecycle.
- **Classification:** **`per_seat` → `supplier_route_per_seat`**, **`full_bus` → `supplier_route_full_bus`**, customer RFQ detail **`custom_bus_rental_request`** — matches Track **5g** three-mode model; **Mode 2** remains catalog (**Layer A**), **Mode 3** remains RFQ (**Layer C**).
- **Tests:** **`test_customer_commercial_mode_read`**, **`test_services_mini_app_tour_detail`** (incl. full-bus), **`test_api_mini_app`** (tour detail), **`test_custom_marketplace_track5f_v1`** (**`commercial_mode`** on detail); regressions **`test_custom_marketplace_track5a`**, **`test_custom_request_booking_bridge_track5e`**, **`test_custom_marketplace_track4`** — **pass** (focused acceptance run).

### Status
**closed** for **Track 5g.1** scope (read-side classification + documentation) — **stabilization reviewed**.

---

## 36. V2 Tracks 5g.4a–5g.4e — Catalog Mode 2 Mini App path (closure)

### Intent
- Record **acceptance** that **standalone catalog Mode 2** (virgin whole-bus catalog self-serve on **Layer A**) is **implemented and closed** through **5g.4d**; **5g.4e** is documentation-only.
- **Not** Mode 3 (RFQ), **not** bridge execution changes, **not** payment reconciliation redesign.

### Single source of truth for scope
- **`docs/TRACK_5G4_MODE2_ACCEPTANCE_SUMMARY.md`** — implemented slices, user behavior, non-goals, postponed items, test pointers.

### Non-regression boundaries (verified by track constraints)
- **Mode 1** per-seat semantics; **RFQ/bridge** execution; **`PaymentReconciliationService`**; supplier marketplace **admin/supplier** flows beyond shared **Layer A** reads; **charter pricing model**; **waitlist/handoff** workflows — **unchanged in meaning** by **5g.4** (presentation + narrow read/formatting only where documented in that summary).

### Status
**closed** for **Tracks 5g.4a–5g.4e** — reopen only for **regressions** or **security**; forward product work is **outside** this branch (see acceptance doc **Postponed**).
