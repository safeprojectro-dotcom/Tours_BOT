# Chat Handoff

## Project
Tours_BOT

## Current Status
Project is continuing in a new chat from the latest approved checkpoint.

## Current Phase
Phase 4 / Step 8 completed

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

### Phase 4 Test/Dependency/Cleanup Checkpoint
- missing `httpx` issue was identified as an environment sync issue, not a project dependency-definition issue
- project dependency definition already included `httpx`
- API payment tests now pass
- test-harness cleanup step completed
- `psycopg ResourceWarning` from open pooled connection was removed by centralizing engine disposal in shared DB test base
- cleanup touched test harness only, not production business logic

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
- payment-pending reminder worker tests pass
- `python -m unittest discover -s tests/unit -v` currently passes
- latest known status: 64/64 unit tests passed
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
- payment-pending reminder slice passes tests
- notification preparation, dispatch, and reminder logic remain service-layer driven
- no real notification delivery has been added yet

---

## Current Architecture State

### Ready
- models
- migrations
- repositories
- Pydantic schemas
- read services
- preparation services
- private bot foundation
- multilingual private entry foundation
- guided private browsing flow
- reservation-preparation flow
- temporary reservation creation flow
- payment entry flow
- payment reconciliation core service
- payment webhook/API delivery slice
- reservation expiry worker
- notification preparation foundation
- notification dispatch foundation
- payment-pending reminder worker slice
- clean DB-backed unit test harness

### Not Implemented Yet
- real `telegram_private` notification delivery
- broader reminder workers and scheduling/orchestration
- refund workflow
- waitlist actions/workflow
- handoff lifecycle workflow
- Telegram group behavior
- Mini App UI
- admin workflows
- content publication workflows

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
- no waitlist actions yet
- no handoff actions yet
- no group logic yet
- no Mini App UI yet

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
- real `telegram_private` notification delivery
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
- notification event/type definitions
- channel-specific dispatch envelope preparation for `telegram_private`
- deterministic dispatch key generation for prepared dispatches
- due reminder selection for active reservations approaching expiry
- first payment-pending reminder worker slice

### Not yet implemented
- real `telegram_private` notification sending
- outbox persistence / dispatch tracking
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications
- predeparture reminders
- post-trip reminders

---

## Next Safe Step
Phase 4 / Step 9

### Goal
Add the first real `telegram_private` notification delivery slice on top of the existing notification preparation, dispatch, and reminder groundwork, without introducing advanced queue/scheduler complexity.


### Safe scope for next step
- add a minimal delivery service or adapter for `telegram_private` only
- deliver already prepared notification dispatches through the Telegram private channel only
- support the currently existing notification groundwork only:
  - prepared notification payloads
  - dispatch envelopes
  - payment-pending reminder outputs
- keep the integration narrow and explicit
- add focused tests for delivery behavior, safe failure handling, and service boundaries
- keep business rules in the service layer
- keep worker and bot wiring thin
- keep API/UI layers untouched unless a minimal integration point is strictly necessary

### Must Not Be Implemented Yet
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications
- full production scheduler/orchestrator
- advanced outbox/queue persistence
- group bot behavior
- Mini App UI
- refund workflow
- advanced admin automation
---

## Recommended Next Prompt
Use this in the new chat:

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, and `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, implement only the first real `telegram_private` notification delivery slice on top of the existing notification preparation, dispatch, and reminder groundwork.

Goal:
Add the first real `telegram_private` notification delivery path without expanding into group delivery, Mini App delivery, waitlist/handoff notifications, or advanced queue/scheduler complexity.

Allowed scope:
- add a minimal delivery service or adapter for `telegram_private` only
- send already prepared notification dispatches through the Telegram private channel only
- support the currently existing notification groundwork only:
  - notification preparation outputs
  - notification dispatch envelopes
  - payment-pending reminder outputs
- add any minimal schemas/helpers needed for delivery results if strictly necessary
- add focused tests for delivery behavior, safe failure handling, and clear service boundaries
- keep business rules in the service layer and keep worker/bot wiring thin

Requirements:
- reuse the existing notification preparation, dispatch, and payment-pending reminder foundations where appropriate
- keep the implementation PostgreSQL-first
- keep delivery limited to `telegram_private`
- do not add group delivery
- do not add Mini App delivery
- do not add waitlist notifications
- do not add handoff notifications
- do not add predeparture reminders yet
- do not add post-trip reminders yet
- do not add full scheduler/orchestrator complexity yet
- do not add advanced outbox persistence or queueing unless it is strictly necessary for the narrow current slice
- keep API/UI layers untouched unless a very small integration point is strictly required
- run the minimal relevant tests first and do not claim broader coverage than what is actually tested

Do not implement yet:
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications
- full production scheduler/orchestrator
- advanced outbox/queue persistence
- group bot behavior
- Mini App UI
- refund workflow
- advanced admin automation

Before writing code:
1. summarize the current project state
2. list what is already completed in Phase 4
3. identify the exact next safe step and explain why it is smaller than broader notification delivery rollout
4. list the services, workers, schemas, adapters, helpers, and tests you will add or extend
5. explain the boundary between notification preparation/dispatch/reminder selection and real Telegram private delivery
6. explain what remains postponed

Then generate the code and tests.

---

## New Chat Startup Prompt
Start this task as a continuation of the current project state, but in a fresh chat.

Use the following as the source of truth for continuity:
- project rules
- current codebase
- docs/TECH_SPEC_TOURS_BOT.md
- docs/IMPLEMENTATION_PLAN.md
- docs/TESTING_STRATEGY.md
- docs/AI_ASSISTANT_SPEC.md
- docs/AI_DIALOG_FLOWS.md
- docs/CHAT_HANDOFF.md

Important continuity rules:
- preserve the existing architecture and phase sequence
- do not repeat already completed work
- do not reintroduce previously postponed logic
- continue from the last approved checkpoint in docs/CHAT_HANDOFF.md

Before doing anything:
1. summarize the current project state
2. list what is already completed
3. identify the exact next safe step
4. list what must NOT be changed yet