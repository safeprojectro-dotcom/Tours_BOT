# Chat Handoff

## Project
Tours_BOT

## Current Status
Project is continuing in a new chat from the latest approved checkpoint.

## Current Phase
Phase 5 (Mini App MVP) — **Phase 5 / Step 9 completed**; **Step 9A:** optional hold TTL via `TEMP_RESERVATION_TTL_MINUTES` (see `docs/PHASE_5_STEP_9_NOTES.md`).

`docs/IMPLEMENTATION_PLAN.md` defines **Phase 5 as a single phase** (no numbered substeps in the plan). The **Step N** labels here are **project execution checkpoints** mapped to Phase 5 *Included Scope* / *Done-When* bullets (UX first, then screens, booking, payment, help/bookings as the phase exit signal).

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

Фаза: Phase 5 / Step 8
Шаг: связка private chat и Mini App в одном staging-сценарии
Сделано: welcome/CTA обновлены, Mini App и My bookings подняты наверх, добавлены /help /bookings /contact, тексты бота и Mini App согласованы, добавлен smoke-checklist
Не трогали: booking/payment rules, API, DB schema, waitlist, handoff, webhook, deploy model
Замечание: один тест падает из-за seeded TEST_BELGRADE_001 в БД, не из-за логики Step 8

ТЕКУЩЕЕ СОСТОЯНИЕ STAGING ПОСЛЕ STEP 8A

Инфраструктура:
- API backend работает на Railway
- Telegram bot работает через Railway webhook, локальный polling больше не нужен для обычной работы
- Mini App UI вынесен в отдельный Railway service и открывается из Telegram
- PostgreSQL на Railway подключен и используется
- Миграции применены
- TEST_BELGRADE_001 seeded в staging

Что уже работает:
- /start, /tours, /bookings, /language, /help, /contact в боте открываются
- кнопка "Deschide Mini App" открывает Mini App
- mobile catalog scroll уже исправлен на главной странице каталога
- View details на мобильном теперь достижим
- webhook flow стабилен, апдейты обрабатываются на Railway

Что выявлено после утреннего smoke-test:
1. Scroll исправлен только на catalog screen; другие Mini App screens ещё не унифицированы:
   - detail page требует scroll
   - prepare page требует scroll
   - booking details / payment / help / settings тоже надо проверить на единый scroll layout
2. UI-shell Mini App не переведён полностью на выбранный язык:
   - сам tour content может fallback-иться на EN, это допустимо
   - но labels/buttons/navigation shell должны переводиться
3. TEST_BELGRADE_001 часто уходит в sold out / seats_available=0 из-за накопленных staging orders/holds/payments
   - из-за этого prepare выдаёт "tour is not available for reservation preparation"
4. В DB есть несколько orders/payments по test tour, но My bookings показывает только одну запись
   - вероятная причина: фильтрация по current user_id или по статусу
   - это нужно явно проверить и задокументировать

Что нельзя потерять:
- Не менять booking/payment business rules
- Не менять DB schema / migrations
- Не ломать webhook / Railway deploy model
- Не убирать отдельный Mini App UI service
- Все fixes должны быть staging-safe и обратимыми

Следующий правильный шаг:
- Step 8B stabilization:
  1) общий scroll pattern для всех Mini App pages
  2) перевод Mini App UI-shell
  3) audit/reset test-tour availability
  4) audit why My bookings shows only one record

РЕШЕНИЕ ПОСЛЕ STEP 8B

Текущее решение:
- Сейчас НЕ меняем reservation/payment business logic.
- Сначала восстанавливаем чистый staging-state для TEST_BELGRADE_001, потому что основной smoke-flow стал невоспроизводим из-за накопленных test orders/payments/holds.
- Проблема prepare сейчас трактуется как data hygiene issue staging, а не как доказанный дефект Mini App UI.
- My bookings vs many orders in DB трактуется как expected current-user filtering, если не доказано обратное.

Что делать сейчас:
1. Починить / стабилизировать reset TEST_BELGRADE_001
2. Вернуть тур в состояние:
   - status = open_for_sale
   - seats_available = seats_total
   - без активных test orders/payments/holds для этого тура
3. Повторно прогнать smoke:
   - catalog
   - detail
   - prepare
   - one hold creation
   - my bookings
   - payment page

Что делать позже отдельным этапом:
- review reservation lifecycle как бизнес-логики:
  - hold TTL
  - auto-release expired holds
  - anti-false-sold-out behavior
  - правила отображения expired/released bookings
Это уже заложено в архитектуре (temporary reservation / payment entry / expiry), но будет рассматриваться позже как отдельный продуктовый этап, а не в рамках текущего UI stabilization.

ТЕКУЩЕЕ СОСТОЯНИЕ ПОСЛЕ STEP 8A / 8B / 8C

Инфраструктура:
- API backend работает на Railway
- Telegram bot переведён на Railway webhook
- Mini App UI вынесен в отдельный Railway service и открывается из Telegram
- PostgreSQL Railway подключен и используется как staging DB
- Миграции применены
- TEST_BELGRADE_001 seeded и обслуживается как staging-only test tour

Что подтверждено вручную:
- /start, /tours, /bookings, /language, /help, /contact работают
- кнопка "Deschide Mini App" открывает реальный Mini App UI
- catalog screen на mobile скроллится
- detail screen скроллится
- View details работает
- Prepare reservation работает после очистки staging data
- создаётся temporary reservation / hold
- создаётся payment entry
- запись появляется в Railway Postgres:
  - orders
  - payments
- seats_available уменьшается корректно
- My bookings показывает бронирование текущего пользователя

Что было важно выяснить:
- проблема "tour is not available for reservation preparation" была вызвана не поломкой Mini App, а загрязнёнными staging test-data
- проблема "в БД много orders, а в My bookings одна запись" трактуется как expected current-user filtering
- Mini App shell переводится, но контент тура может fallback-иться по backend rules

Что сделано для staging hygiene:
- reset_test_belgrade_tour_state.py теперь реально очищает TEST_BELGRADE_001 в Railway staging DB
- reset удаляет связанные orders/payments/notification artifacts по test tour
- после reset:
  - status = open_for_sale
  - seats_available = seats_total
  - prepare снова доступен
- перед повторным full smoke staging tour при необходимости нужно reset-ить

Технический инцидент:
- mini_app/ui_layout.py не был закоммичен в git и из-за этого Mini_App_UI падал на Railway
- scrollable_page перенесён в mini_app/app.py
- отдельный import mini_app.ui_layout больше не использовать без явного коммита файла

Что НЕ трогали:
- booking/payment core business rules
- DB schema / migrations
- webhook model
- Railway split API / Mini App UI

Следующий шаг:
- Step 9: reservation/payment lifecycle stabilization
- focus:
  - hold TTL
  - expiry / auto-release
  - release of seats back to sale
  - status transitions in booking/payment lifecycle
  - consistent user-facing statuses in Mini App

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
- latest known status: full unit suite passed at Phase 5 / Step 4 checkpoint (update count on next run)
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
- `telegram_private` notification delivery slice
- payment-pending reminder worker slice
- payment-pending reminder delivery slice
- notification outbox persistence foundation
- payment-pending reminder outbox slice
- notification outbox processing slice
- notification outbox recovery slice
- notification outbox retry execution slice
- predeparture reminder groundwork
- predeparture reminder outbox slice
- departure-day reminder groundwork
- departure-day reminder outbox slice
- post-trip reminder groundwork
- post-trip reminder outbox slice
- clean DB-backed unit test harness

### Not Implemented Yet
- broader reminder workers and scheduling/orchestration
- refund workflow
- waitlist actions/workflow
- handoff lifecycle workflow
- Telegram group behavior
- Mini App: real reservation creation, payment UI, my bookings, auth/init, help/operator flows (Phase 5 remaining scope per `docs/IMPLEMENTATION_PLAN.md`)
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

### Mini App constraints (latest checkpoint)
- catalog, filters, read-only tour detail, reservation **preparation** UI only
- no real reservation creation or payment flow in the Mini App yet (next Phase 5 work per implementation plan)

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
- due reminder selection for active reservations approaching expiry
- first payment-pending reminder worker slice
- payment-pending reminder delivery and outbox slices
- notification outbox persistence / pending entry tracking
- notification outbox processing, recovery, and retry execution
- predeparture reminder selection and outbox enqueue groundwork
- departure-day reminder selection and outbox enqueue groundwork
- post-trip reminder selection and outbox enqueue groundwork

### Not yet implemented
- group delivery
- Mini App delivery
- waitlist notifications
- handoff notifications

---

## Next Safe Step
Phase 5 / Step 9

**Plan alignment (`docs/IMPLEMENTATION_PLAN.md` Phase 5):** the phase exit signal is *“Mini App UX defined first, then screens, booking, payment, and help flow implemented”*. The next **Included Scope** items not yet satisfied after Step 4 are the **reserve action** and **payment** slices: *“Build reservation screen for seat count, boarding point, reservation timer, and reserve action”* and *“Build payment screen with amount, timer, and transition into payment scenario”*, matching *Done-When*: *“reserve seats, start payment”*. Step 4 completed only preparation UI; Step 5 implements **real temporary reservation creation** and **starting payment** in the Mini App by reusing existing Phase 3–4 service-layer flows (`TemporaryReservationService`, `PaymentEntryService`, reconciliation assumptions), not by duplicating rules in the UI.

### Goal
Deliver the Mini App **reserve** action and **start payment** flow on top of the existing foundation (catalog, filters, tour detail, reservation preparation UI), until a user can create a temporary reservation and enter the payment step consistent with the private bot behavior.

### Safe scope for next step
- wire Mini App to create a **temporary reservation** (order) using existing reservation creation services and validations
- wire Mini App to **continue to payment** / payment entry for that reservation using existing payment-entry behavior
- surface **reservation timer** and amount/expiry in UI where the plan expects them for reservation and payment screens
- add only **minimal** Mini App API endpoints if needed; keep business rules in services
- add focused tests for new endpoints or adapters, not for re-proving Phase 3–4 core logic

### Must not expand yet (unless `IMPLEMENTATION_PLAN.md` / spec explicitly pulls them in)
- waitlist workflow
- handoff/operator workflow
- **Mini App auth/init with Telegram context** (listed in Phase 5 scope; keep postponed until explicitly scheduled—do not block reserve/payment on it if the narrow slice can use the same assumptions as current dev Mini App)
- my bookings / booking status screen (plan *Done-When* also mentions *“later view booking status”*—can be a follow-up checkpoint if reserve+pay is large)
- unrelated admin, group, or content work

## Recommended Next Prompt
Use this in the new chat:

Using `docs/TECH_SPEC_TOURS_BOT.md`, `docs/IMPLEMENTATION_PLAN.md` (Phase 5 *Included Scope* and *Done-When*), `docs/TESTING_STRATEGY.md`, `docs/AI_ASSISTANT_SPEC.md`, `docs/AI_DIALOG_FLOWS.md`, `docs/CHAT_HANDOFF.md`, `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`, and `docs/MINI_APP_UX.md`, implement **Phase 5 / Step 5**: Mini App **temporary reservation creation** and **payment start** on top of the existing Mini App foundation (catalog, filters, read-only tour detail, reservation preparation UI).

Goal:
Match the implementation plan’s next booking/payment slices: **reserve action** + **payment screen entry** (amount, timer, transition into payment scenario), reusing `TemporaryReservationService`, `PaymentEntryService`, and existing payment/reconciliation assumptions—no duplicated business rules in Flet.

Requirements:
- keep scope narrow: no waitlist, no handoff, no Mini App auth/init expansion unless strictly required for a minimal integration stub
- add minimal API/adapter layer only; services own mutations
- mobile-first; align with `docs/MINI_APP_UX.md`
- add tests for new Mini App-specific glue (routes/adapters), not a rewrite of Phase 3–4 tests

Before writing code:
1. summarize current state and what Phase 5 Steps 1–4 already delivered
2. quote how this maps to `IMPLEMENTATION_PLAN.md` Phase 5 bullets
3. list files/endpoints/UI to add or extend
4. list what remains postponed (my bookings, auth/init, help, etc.)

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