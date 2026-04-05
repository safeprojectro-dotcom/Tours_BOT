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
- admin read-side is established
- narrow admin write slices for tours, boarding points, and translations exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 19

Нужен только один узкий safe slice:
FIRST NARROW ADMIN HANDOFF STATUS MUTATION SLICE

Важно:
это НЕ полный operator workflow engine.
Это только один очень узкий, контролируемый mutation slice для handoff status.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint for minimal handoff status progression.
Предпочтительный вариант:
   - POST /admin/handoffs/{handoff_id}/mark-in-review
   - POST /admin/handoffs/{handoff_id}/close
Но выбери только ОДИН из них для этого шага, не оба сразу.
Предпочтительно:
   - first narrow `mark-in-review` slice
или
   - first narrow `close` slice
Выбери тот, который лучше совпадает с текущей persisted status model и безопаснее вводится первым.

2. Цель шага:
- дать минимально полезную admin action over handoff
- не строить assignment/claim engine
- не открывать широкую state machine handoff statuses

3. Validation / safety rules:
- handoff must exist
- allowed current status transitions must be very narrow and explicit
- operation should be idempotent where reasonably possible
- if current status makes the action invalid, return safe client error
- do not mutate linked order/payment/tour state
- do not add side-effect notifications in this step

4. Response shape:
- return updated AdminHandoffRead
- keep route layer thin
- keep status transition logic in service layer
- keep repositories persistence-oriented only

5. If Step 18 already introduced queue indicators:
- preserve them
- updated handoff detail/read model should still expose queue-friendly fields consistently

Очень важно:
- do not add claim/assign in this step
- do not add both review and close if that widens scope too much
- do not add operator workflow engine
- do not add notifications side effects
- do not touch public handoff creation flow
- do not change booking/payment flows

Разрешённый scope:
- one narrow handoff status mutation only
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- claim/assign
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
- покрыть protected access for chosen handoff mutation endpoint
- покрыть successful status change
- покрыть not-found behavior
- покрыть invalid current status handling
- покрыть idempotent behavior if chosen
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы