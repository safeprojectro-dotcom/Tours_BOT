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
- Phase 6 / Steps 18–22 completed:
  - handoff queue/detail + narrow handoff mutations
- Phase 6 / Step 23 completed:
  - narrow admin operator cancel for active temporary hold
- Phase 6 / Step 24 completed:
  - narrow admin duplicate-marking slice
- Phase 6 / Step 25 completed:
  - narrow admin no-show marking slice
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, handoffs, and order corrections now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 26

Нужен только один узкий safe slice:
FIRST NARROW ADMIN ORDER READY-FOR-DEPARTURE MARKING SLICE

Важно:
это НЕ полный order workflow editor.
Это только один very narrow admin mutation for marking an order as `ready_for_departure` in a conservative way.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - POST /admin/orders/{order_id}/mark-ready-for-departure

2. Цель шага:
- дать админу минимально полезную предвыездную ручную операцию по заказу
- не открывать широкий редактор статусов
- не трогать provider/payment reconciliation
- не менять публичную booking/payment логику

3. Validation / safety rules:
- order must exist
- choose the narrowest safe rule for when `ready_for_departure` is allowed
- prefer allowing only a confirmed + paid + active order
- if current state makes this unsafe, return safe client error
- consider whether departure must be in the future or within a small safe window; choose the narrower rule and document it explicitly
- do not mutate payment rows
- do not rewrite reconciliation semantics
- do not change seats in this step

4. Scope of state change:
- prefer changing only `booking_status -> ready_for_departure`
- keep `payment_status` unchanged
- keep `cancellation_status` unchanged unless absolutely necessary and explicitly justified
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
- do not add broad order status editor
- do not add refund workflow
- do not add move-to-another-tour/date
- do not change webhook behavior
- do not touch public booking/payment flows
- do not widen into notification workflow in this step

Разрешённый scope:
- one narrow admin order ready-for-departure mutation only
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- payment mutation
- refund workflow
- broad order workflow editor
- move/merge tooling
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
- покрыть successful ready-for-departure marking
- покрыть not-found behavior
- покрыть invalid current status handling
- покрыть idempotent behavior if chosen
- покрыть chosen departure-time rule explicitly
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed