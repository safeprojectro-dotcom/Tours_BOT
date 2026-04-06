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
- Phase 6 / Step 19 completed:
  - POST /admin/handoffs/{handoff_id}/mark-in-review
- Phase 6 / Step 20 completed:
  - POST /admin/handoffs/{handoff_id}/close
- Phase 6 / Step 21 completed:
  - POST /admin/handoffs/{handoff_id}/assign
- Phase 6 / Step 22 completed:
  - POST /admin/handoffs/{handoff_id}/reopen
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, and handoff workflow now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 23

Нужен только один узкий safe slice:
FIRST NARROW ADMIN ORDER STATUS MUTATION SLICE

Важно:
это НЕ полный order workflow editor.
Это только один very narrow admin order mutation for one clearly justified status transition.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint for minimal order status intervention.
Предпочтительный вариант:
- POST /admin/orders/{order_id}/mark-cancelled-by-operator
или другой equally narrow endpoint, но только ОДИН.

Предпочтительно выбрать именно:
- операторская отмена заказа / брони по узкому правилу,
потому что это проще и безопаснее, чем подтверждать оплату, refund, move, duplicate-merge и т.д.

2. Цель шага:
- дать админу минимально полезную корректирующую операцию по заказу
- не открывать широкий editor всех booking/cancellation/payment statuses
- не трогать provider/payment reconciliation

3. Validation / safety rules:
- order must exist
- transition must be very narrow and explicit
- change only what is absolutely needed to represent operator cancellation safely
- do not mark payment as paid/unpaid by guess
- do not bypass reconciliation semantics
- if current status makes this action invalid, return safe client error
- operation may be idempotent if already in the same terminal cancellation state
- if seat restoration is needed by current business semantics, choose the narrowest safe rule and document it explicitly
- if seat restoration is too risky for this step, reject unsafe cases rather than guessing

4. Scope of state change:
- prefer changing only cancellation-related state and any absolutely necessary booking/user-visible state
- keep payment state untouched unless already explicitly required by safe existing semantics
- do not change tour/payment/handoff entities beyond what is strictly necessary

5. Response shape:
- return updated AdminOrderDetailRead
- preserve lifecycle fields and correction visibility fields
- preserve action preview fields
- keep route layer thin
- keep transition logic in service layer
- keep repositories persistence-oriented only

Очень важно:
- do not add refund/capture/cancel-payment
- do not add broad order status editor
- do not add move-to-another-tour/date
- do not rewrite reconciliation logic
- do not change webhook behavior
- do not touch public booking/payment flows

Разрешённый scope:
- one narrow admin order mutation only
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- payment mutation
- refund workflow
- broad order workflow editor
- move/duplicate merge
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
- покрыть successful status change
- покрыть not-found behavior
- покрыть invalid current status handling
- покрыть idempotent behavior if chosen
- покрыть chosen seat-restoration policy if applicable
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed