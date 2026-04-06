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
- Phase 6 / Steps 1–15 completed:
  - protected admin foundation
  - tours CRUD-like narrow slices
  - boarding point CRUD-like narrow slices
  - tour and boarding point translations narrow slices
  - archive/unarchive for tours
- Phase 6 / Step 16 completed:
  - read-only admin order/payment correction visibility
- Phase 6 / Step 17 completed:
  - read-only admin action preview on order detail
- Phase 6 / Step 18 completed:
  - read-only admin handoff queue visibility/detail
- Phase 6 / Steps 19–22 completed:
  - narrow handoff mutations:
    - mark-in-review
    - close
    - assign
    - reopen
- Phase 6 / Step 23 completed:
  - narrow admin operator cancel for active temporary hold
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, handoffs, and one order correction mutation now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 24

Нужен только один узкий safe slice:
FIRST NARROW ADMIN ORDER DUPLICATE-MARKING SLICE

Важно:
это НЕ полный order workflow editor.
Это только один very narrow admin mutation for marking an order as duplicate.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - POST /admin/orders/{order_id}/mark-duplicate

2. Цель шага:
- дать админу минимально полезную ручную корректировку для явно лишнего / дублирующего заказа
- не открывать широкий редактор всех order statuses
- не трогать provider/payment reconciliation
- не делать merge workflow

3. Validation / safety rules:
- order must exist
- transition must be very narrow and explicit
- choose the narrowest safe rule for when duplicate-marking is allowed
- if current state makes this unsafe, return safe client error
- do not mark paid orders as duplicate in this step unless there is an extremely strong, narrow, and explicitly documented reason
- do not mutate payment records
- do not rewrite reconciliation semantics
- if seat restoration is needed, choose the narrowest safe rule and document it explicitly
- if seat restoration is too risky for a specific state, reject that state rather than guessing

4. Scope of state change:
- prefer changing only `cancellation_status -> duplicate`
- and any absolutely necessary related fields
- keep `booking_status` / `payment_status` changes minimal and explicitly justified
- do not affect tour/payment/handoff entities beyond what is strictly needed

5. Response shape:
- return updated `AdminOrderDetailRead`
- preserve lifecycle fields
- preserve correction visibility fields
- preserve action preview fields
- keep route layer thin
- keep transition logic in service layer
- keep repositories persistence-oriented only

Очень важно:
- do not add order merge tooling
- do not add broad order status editor
- do not add payment mutation
- do not add refund workflow
- do not add move-to-another-tour/date
- do not change webhook behavior
- do not touch public booking/payment flows

Разрешённый scope:
- one narrow admin order duplicate mutation only
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- payment mutation
- refund workflow
- broad order workflow editor
- merge tooling
- publication workflow
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
2. перечисли endpoint(s)
3. перечисли schemas/services/repository changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть protected access for chosen order mutation endpoint
- покрыть successful duplicate-marking
- покрыть not-found behavior
- покрыть invalid current status handling
- покрыть chosen seat-restoration policy if applicable
- покрыть idempotent behavior if chosen
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed