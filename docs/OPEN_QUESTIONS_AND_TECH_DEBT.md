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
- **Database fields are unchanged:** the combination described in **section 1** (`booking_status` may remain `reserved` after expiry, etc.) still exists at persistence layer.

### Why core debt remains open
- Raw status **semantics** in section 1 are still the source of truth for storage and workers; projection only helps **read** surfaces that use it.
- **Admin mutations**, **reporting**, **analytics**, or dashboards that filter on raw enums **without** the same projection rules can still misinterpret state.

### Revisit trigger
- before **admin mutation** flows (status changes, cancellations, manual fixes)
- before **richer admin reporting** or exports that aggregate by raw status
- before **analytics / dashboards** depend directly on raw status combinations without a documented projection layer

### Status
open (read-side **partially mitigated** for Phase 6 Step 1 list API; **section 1** remains open for semantics and non-projected consumers)

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