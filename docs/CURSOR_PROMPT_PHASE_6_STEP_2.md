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
- Phase 6 / Step 1 already completed
- protected admin foundation already exists
- token-protected read-only admin API already exists:
  - GET /admin/overview
  - GET /admin/tours
  - GET /admin/orders
- safe lifecycle projection already exists for admin order list
- Railway verification already passed
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 2

Нужен только один узкий safe slice:
READ-ONLY ADMIN ORDER DETAIL VISIBILITY

Что именно сделать:
1. Добавить read-only endpoint:
   - GET /admin/orders/{order_id}
2. Добавить admin order detail DTO / schemas
3. Показать в detail только read-side visibility:
   - order core fields
   - user_id
   - tour summary
   - boarding point summary if available
   - seats_count
   - total_amount / currency
   - booking/payment/cancellation raw states if needed internally in DTO
   - safe human-readable lifecycle_kind / lifecycle_summary
   - reservation_expires_at
   - created_at / updated_at
   - payment records summary or latest payments if safely available
   - linked handoff summary if safely available
4. Reuse existing repositories/services as much as possible
5. Keep route layer thin
6. Keep repositories persistence-oriented only
7. Keep business/status interpretation in service layer

Очень важно:
docs/OPEN_QUESTIONS_AND_TECH_DEBT.md already records that expired reservations may look ambiguous if raw status combinations are exposed.
Therefore:
- do not leak ambiguous raw status combinations as the main admin meaning
- lifecycle_kind / lifecycle_summary must remain the primary admin-facing interpretation
- this step should reinforce safe admin read-side behavior, not bypass it

Разрешённый scope:
- one new read-only admin detail endpoint
- new admin detail schema(s)
- minimal read-side service expansion
- focused tests for endpoint and status/detail projection

Запрещено в этом шаге:
- tour CRUD
- translations CRUD
- boarding points CRUD
- manual order mutation
- payment mutation / refunds
- handoff mutation flows
- content/publication admin features
- broad refactor
- public booking/payment/waitlist/handoff changes
- frontend/admin SPA expansion

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли endpoint(s)
3. перечисли schemas/services/repository changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть protected access for GET /admin/orders/{order_id}
- покрыть successful read of admin order detail
- покрыть not-found behavior
- покрыть lifecycle/status projection for expired unpaid reservation pattern if applicable in detail response
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed