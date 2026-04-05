Продолжаем Tours_BOT от последнего approved checkpoint.

Используй как source of truth:
1. docs/IMPLEMENTATION_PLAN.md
2. docs/CHAT_HANDOFF.md
3. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
4. docs/PHASE_5_ACCEPTANCE_SUMMARY.md
5. docs/TESTING_STRATEGY.md
6. docs/AI_ASSISTANT_SPEC.md
7. docs/AI_DIALOG_FLOWS.md
8. docs/TECH_SPEC_TOURS_BOT.md

Контекст:
- Phase 5 accepted for MVP/staging
- Phase 6 / Step 1 completed:
  - protected admin foundation
  - GET /admin/overview
  - GET /admin/tours
  - GET /admin/orders
- Phase 6 / Step 2 completed:
  - GET /admin/orders/{order_id}
- Phase 6 / Step 3 completed:
  - GET /admin/tours/{tour_id}
- Phase 6 / Step 4 completed:
  - read-only filtering expansion for tours/orders
- admin read-side is now reasonably established
- public flows must remain untouched
- no admin mutations yet

Текущая задача:
Phase 6 / Step 5

Нужен только один узкий safe slice:
FIRST VERY NARROW TOURS CRUD SLICE — CREATE ONLY

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - POST /admin/tours
2. Добавить admin create schema(s)
3. Разрешить создать только core tour record:
   - code
   - title_default
   - short_description_default (optional if model allows)
   - full_description_default (optional if model allows)
   - duration_days
   - departure_datetime
   - return_datetime
   - base_price
   - currency
   - seats_total
   - sales_deadline
   - status
   - guaranteed_flag
4. На create:
   - seats_available should be initialized consistently from seats_total unless current domain rules already define another safe behavior
   - validate basic invariants in service layer:
     - return_datetime after departure_datetime
     - seats_total positive or non-negative according to current model expectations
     - sales_deadline must be coherent with departure_datetime at least at a basic safe level
     - code uniqueness handling
5. Return created admin tour read DTO
6. Keep route layer thin
7. Keep business validation in service layer
8. Keep repository persistence-oriented only

Очень важно:
- do not implement full tour management
- do not add update/delete/archive in this step
- do not add translations CRUD in this step
- do not add boarding points CRUD in this step
- do not widen this into media management
- do not change public catalog/business logic beyond safe tour creation persistence
- do not move business rules into route handlers

Разрешённый scope:
- one create endpoint only
- create schema(s)
- minimal service/repository expansion needed for create
- focused tests for create flow

Запрещено в этом шаге:
- update/delete/archive endpoints
- translations CRUD
- boarding points CRUD
- order/payment/handoff mutations
- content/publication features
- frontend/admin SPA expansion
- broad refactor
- public booking/payment/waitlist/handoff changes

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли endpoint
3. перечисли schemas/services/repository changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть protected access for POST /admin/tours
- покрыть successful create
- покрыть duplicate code handling
- покрыть basic validation failure(s)
- проверить, что seats_available initializes safely
- не переписывать старые test slices без причины

Ожидаемый HTTP shape:
- success: created entity returned as admin-facing tour read DTO
- duplicate code: safe client error
- validation failures: safe client error
- unauthorized: consistent with existing /admin protection

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed