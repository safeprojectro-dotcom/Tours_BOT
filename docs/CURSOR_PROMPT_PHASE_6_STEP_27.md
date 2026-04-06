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
  - narrow admin order corrections:
    - mark-cancelled-by-operator
    - mark-duplicate
    - mark-no-show
    - mark-ready-for-departure
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, handoffs, and order corrections now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 27

Нужен только один узкий safe slice:
FIRST NARROW ADMIN ORDER LIFECYCLE-READ REFINEMENT SLICE

Важно:
это НЕ новая order mutation.
Это read-side refinement only.

Что именно сделать:
1. Refine admin lifecycle interpretation so that `ready_for_departure` no longer falls into generic `other`, if that is currently the case.
2. Keep lifecycle changes extremely narrow and explicitly documented.
3. Update only the minimal read-side/service logic needed.

Цель шага:
- make admin order detail/list more operationally meaningful after Step 26
- keep existing mutation surfaces unchanged
- avoid broad lifecycle rewrite

Validation / safety rules:
- no mutation endpoints added
- no order/payment/handoff state changes
- no reconciliation changes
- no public flow changes
- keep existing lifecycle semantics stable except for the narrow refinement needed for `ready_for_departure`

Response/model scope:
- reuse existing lifecycle fields
- if a new lifecycle kind is absolutely necessary, introduce the narrowest safe extension
- if existing lifecycle summary can be refined without a new enum, prefer the narrower option
- keep route layer unchanged where possible
- keep interpretation logic in service layer / lifecycle service
- keep repositories untouched unless strictly necessary

Очень важно:
- do not widen into a broad lifecycle redesign
- do not change order mutation semantics
- do not touch public booking/payment flows
- do not change action preview logic beyond what is necessary to stay consistent with the refined lifecycle meaning

Разрешённый scope:
- one narrow read-side lifecycle refinement only
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
2. перечисли lifecycle/read-side changes
3. перечисли schema/service changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть existing admin order detail/read paths affected by lifecycle refinement
- покрыть ready_for_departure case explicitly
- покрыть that older lifecycle interpretations are not unintentionally broken
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие read-side changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed