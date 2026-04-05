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
  - read-only admin order detail visibility
- admin read-side now covers overview, tours list, orders list, order detail
- public flows must remain untouched
- no admin CRUD yet

Текущая задача:
Phase 6 / Step 3

Нужен только один узкий safe slice:
READ-ONLY ADMIN TOUR DETAIL VISIBILITY

Что именно сделать:
1. Добавить read-only endpoint:
   - GET /admin/tours/{tour_id}
2. Добавить admin tour detail DTO / schemas
3. В detail показать только read-side operational visibility:
   - core tour fields
   - code
   - title_default
   - departure/return datetime
   - price/currency
   - seats_total
   - seats_available
   - sales_deadline
   - status
   - guaranteed_flag
   - created_at / updated_at
   - translations summary if safely available
   - boarding points summary if safely available
   - high-level recent order counts / visibility only if safely derivable without broadening scope
4. Reuse existing repositories/services where possible
5. Keep route layer thin
6. Keep repositories persistence-oriented
7. Keep business interpretation in service layer / schema mapping if needed

Разрешённый scope:
- one new read-only admin detail endpoint
- new admin tour detail schema(s)
- minimal repository/service expansion for read-side
- focused tests

Запрещено в этом шаге:
- tour mutations / CRUD
- translation CRUD
- boarding point CRUD
- order mutations
- payment mutations
- handoff mutations
- content/publication admin features
- frontend/admin SPA expansion
- public booking/payment/waitlist/handoff changes
- broad refactor

Важно:
- this is read-only visibility only
- do not accidentally introduce edit semantics
- do not move business logic into route layer
- do not widen this into “tour management”

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
- покрыть protected access for GET /admin/tours/{tour_id}
- покрыть successful read of admin tour detail
- покрыть not-found behavior
- при наличии translations / boarding points покрыть корректное включение их summary
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed