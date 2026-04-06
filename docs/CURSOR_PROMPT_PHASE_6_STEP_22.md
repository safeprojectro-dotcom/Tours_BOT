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
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, and handoff status/assignment now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 22

Нужен только один узкий safe slice:
FIRST NARROW ADMIN HANDOFF REOPEN-ONLY SLICE

Важно:
это НЕ полный operator workflow engine.
Это только один very narrow mutation slice for reopening a handoff after it was closed.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - POST /admin/handoffs/{handoff_id}/reopen

2. Цель шага:
- дать минимально полезный способ вернуть handoff из `closed` обратно в рабочий queue-state
- не строить широкий workflow engine
- не открывать claim/assign/reassign redesign
- не менять public handoff creation behavior

3. Validation / safety rules:
- handoff must exist
- allowed current transition must be very narrow and explicit
- предпочтительная узкая семантика:
  - `closed -> open`
  - `open -> idempotent success`
  - `in_review -> 400`
- если выберешь другую семантику, она должна быть не шире и явно задокументирована в коде/тестах
- do not mutate linked order/payment/tour state
- do not add side-effect notifications
- do not clear assigned_operator_id unless это уже минимально согласованная и явно обоснованная narrow policy
- если assignment сохраняется при reopen — зафиксируй это явно и последовательно

4. Response shape:
- return updated AdminHandoffRead
- preserve queue-friendly fields from Step 18
- keep route layer thin
- keep transition logic in service layer
- keep repositories persistence-oriented only

5. Preserve consistency with Steps 19–21:
- Step 19 introduced `mark-in-review`
- Step 20 introduced `close`
- Step 21 introduced narrow `assign`
- Step 22 should complement them narrowly, not redesign the workflow

Очень важно:
- do not add unassign in this step
- do not add reassignment redesign in this step
- do not add operator workflow engine
- do not add notifications side effects
- do not touch public handoff creation flow
- do not change booking/payment flows

Разрешённый scope:
- one narrow handoff reopen mutation only
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- unassign
- broader reassignment policy rewrite
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
- покрыть protected access for `POST /admin/handoffs/{handoff_id}/reopen`
- покрыть successful reopen from allowed prior state
- покрыть idempotent behavior if chosen
- покрыть not-found behavior
- покрыть invalid current status handling
- покрыть agreed assignment preservation policy if applicable
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed