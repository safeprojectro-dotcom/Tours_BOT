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
- Phase 6 / Steps 23–26 completed:
  - narrow admin order corrections and pre-trip mutation slices
- Phase 6 / Step 27 completed:
  - narrow read-side lifecycle refinement for `ready_for_departure_paid`
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, handoffs, and order corrections now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 28

Нужен только один узкий safe slice:
FIRST NARROW ADMIN ORDER MOVE-TO-ANOTHER-TOUR/DATE READINESS DECISION SLICE

Важно:
это НЕ сама move mutation.
Это only a narrow read/decision-support slice to determine whether move-like admin work is even safe enough to introduce later.

Что именно сделать:
1. Extend admin order detail narrowly with one conservative move-readiness signal, for example:
   - `move_readiness_hint`
   - `can_consider_move`
   - `move_blockers`
Choose the narrowest shape that fits the current model.

2. Goal:
- help admin understand whether an order might be safely considered for future move-to-another-tour/date handling
- do not actually move anything
- do not mutate order/payment/tour state
- do not introduce workflow complexity too early

3. Logic must be conservative and grounded in existing persisted data only:
- current order statuses
- payment status
- cancellation status
- linked tour timing if needed
- current lifecycle and correction/action-preview fields
- if uncertain, return conservative blocker/manual-review guidance

4. Validation / safety rules:
- read-only only
- no route additions unless absolutely necessary; prefer extending existing `GET /admin/orders/{order_id}`
- no payment mutations
- no seat mutations
- no reconciliation changes
- no public flow changes

5. Response shape:
- prefer extending `AdminOrderDetailRead`
- keep lifecycle and action-preview primary/consistent
- keep interpretation logic in service layer
- keep repositories persistence-oriented only

Очень важно:
- do not add actual move endpoint in this step
- do not add broad workflow engine
- do not add refund or payment corrections
- do not touch public booking/payment flows

Разрешённый scope:
- one narrow read-only decision-support slice
- minimal schema/service/test changes
- focused tests only

Запрещено в этом шаге:
- move mutation
- payment mutation
- refund workflow
- broad order workflow editor
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
2. перечисли read-side/model changes
3. перечисли service/schema changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть affected admin order detail path
- покрыть at least one case that is clearly blocked for move consideration
- покрыть at least one case that is conservatively eligible for consideration if that concept is introduced
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие read-side changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed