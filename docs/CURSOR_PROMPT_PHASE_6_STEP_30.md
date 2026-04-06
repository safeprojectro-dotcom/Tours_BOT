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
  - narrow lifecycle refinement for `ready_for_departure_paid`
- Phase 6 / Step 28 completed:
  - narrow move-readiness decision-support
- Phase 6 / Step 29 completed:
  - narrow admin order move mutation
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, handoffs, and order corrections now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 30

Нужен только один узкий safe slice:
FIRST NARROW ADMIN ORDER MOVE/HISTORY VISIBILITY SLICE

Важно:
это НЕ новая mutation.
Это read-only visibility for already completed admin move operations.

Что именно сделать:
1. Extend admin order detail narrowly with move/history visibility derived from persisted order state and existing timestamps/context.
2. If there is not enough persisted move-history data for a real history timeline, do the narrowest safe version:
   - expose a lightweight `move_snapshot`
   - or `persistence_snapshot`
   - or similarly named read-only block
that makes post-move admin inspection easier without inventing fake history.

3. Goal:
- help admin understand the current persisted post-move state more clearly
- make move result inspection easier after Step 29
- do not invent an audit/history subsystem if the DB does not support it

4. Validation / safety rules:
- read-only only
- no new mutation endpoints
- no fake history records
- no reconciliation changes
- no public flow changes
- if historical reconstruction is not safely grounded, explicitly keep it to current-state snapshot only

5. Response shape:
- prefer extending `AdminOrderDetailRead`
- keep current lifecycle, correction, action preview, and move-readiness fields intact
- add only the minimum extra structure needed for move inspection
- keep route layer unchanged where possible
- keep interpretation logic in service layer
- keep repositories persistence-oriented only

Очень важно:
- do not add audit engine in this step
- do not add broad move timeline subsystem
- do not add payment mutation
- do not touch public booking/payment flows

Разрешённый scope:
- one narrow read-only move inspection slice
- minimal schema/service/test changes
- focused tests only

Запрещено в этом шаге:
- new mutation endpoints
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
- покрыть one moved-order inspection case
- покрыть one non-moved stable case
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие read-side changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed