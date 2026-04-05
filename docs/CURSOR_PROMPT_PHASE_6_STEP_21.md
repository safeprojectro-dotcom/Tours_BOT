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
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, and narrow handoff status progression exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 21

Нужен только один узкий safe slice:
FIRST NARROW ADMIN HANDOFF CLAIM / ASSIGN SLICE

Важно:
это НЕ полный operator workflow engine.
Это только один very narrow mutation slice for ownership/assignment visibility.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint.
Предпочтительный вариант:
- POST /admin/handoffs/{handoff_id}/assign

2. Scope of this step:
- allow assigning one handoff to one operator/admin actor identifier
- keep it extremely narrow
- no re-open
- no status workflow redesign
- no notifications side effects

3. Assignment semantics:
- handoff must exist
- allowed assignment must be explicit and narrow
- prefer operating only on non-closed handoffs
- closed handoff assignment should return safe client error
- repeated assignment to the same operator may be idempotent if chosen
- changing assignment from one operator to another should be either explicitly allowed or explicitly rejected — choose the narrower safer rule and document it
- if current data model stores `assigned_operator_id`, reuse it
- do not invent a broader agent/queue system

4. Input shape:
- minimal request body, only what is necessary
- e.g. `assigned_operator_id`
- no extra workflow fields

5. Response shape:
- return updated AdminHandoffRead
- preserve queue-friendly fields from Step 18
- keep route layer thin
- keep transition/assignment logic in service layer
- keep repositories persistence-oriented only

Очень важно:
- do not add claim + assign + close all together
- do not add operator workflow engine
- do not add notifications side effects
- do not touch public handoff creation flow
- do not change booking/payment flows
- do not widen into RBAC redesign

Разрешённый scope:
- one narrow assignment mutation only
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- reopen
- broad handoff workflow
- order/payment mutations
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
- покрыть protected access for chosen handoff assignment endpoint
- покрыть successful assignment
- покрыть not-found behavior
- покрыть invalid current status handling for closed handoff
- покрыть chosen assignment policy (idempotent same operator / reject reassignment if that is the chosen narrow rule)
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed