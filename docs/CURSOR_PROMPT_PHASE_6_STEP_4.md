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
- admin read-side now covers overview, tours list/detail, orders list/detail
- public flows must remain untouched
- no admin CRUD yet

Текущая задача:
Phase 6 / Step 4

Нужен только один узкий safe slice:
READ-ONLY ADMIN FILTERING EXPANSION

Что именно сделать:
1. Расширить только read-only list endpoints:
   - GET /admin/tours
   - GET /admin/orders
2. Добавить безопасные query parameters для narrow filtering:
   - для `/admin/tours`:
     - `status`
     - `guaranteed_only`
   - для `/admin/orders`:
     - `lifecycle_kind`
     - `tour_id`
3. Реализовать фильтрацию только на backend read-side
4. Сохранить existing response shapes backward-compatible
5. Reuse repositories/services where possible
6. Keep route layer thin
7. Keep status interpretation in service layer

Очень важно:
- `lifecycle_kind` is admin-facing derived meaning, not a raw DB enum
- filtering by `lifecycle_kind` must use the same safe lifecycle projection logic already introduced for admin orders
- do not introduce mutation semantics
- do not widen this into search/sort/reporting platform work

Разрешённый scope:
- read-only query param expansion for existing list endpoints
- minimal repository/service changes
- focused tests for filtered responses

Запрещено в этом шаге:
- any CRUD mutations
- translations CRUD
- boarding points CRUD
- order/payment mutations
- refunds
- handoff mutations
- content/publication features
- SPA/admin frontend expansion
- public booking/payment/waitlist/handoff changes
- broad refactor

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли endpoint changes
3. перечисли schemas/services/repository changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть auth for filtered admin endpoints
- покрыть `/admin/tours?status=...`
- покрыть `/admin/tours?guaranteed_only=true`
- покрыть `/admin/orders?lifecycle_kind=...`
- покрыть `/admin/orders?tour_id=...`
- не ломать существующие unfiltered responses
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие endpoint changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed