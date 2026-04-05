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
  - one narrow handoff status mutation:
    - POST /admin/handoffs/{handoff_id}/mark-in-review
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, and first handoff status mutation exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 20

Нужен только один узкий safe slice:
FIRST NARROW ADMIN HANDOFF CLOSE-ONLY SLICE

Важно:
это НЕ полный operator workflow engine.
Это только один very narrow mutation slice for handoff close semantics.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - POST /admin/handoffs/{handoff_id}/close

2. Цель шага:
- дать минимально полезное завершение handoff lifecycle после Step 19
- не строить claim/assign engine
- не открывать широкую handoff state machine

3. Validation / safety rules:
- handoff must exist
- allowed current transition must be very narrow and explicit
- preferred narrow rule:
  - `in_review -> closed`
  - `closed -> idempotent success`
  - `open -> 400`
- if you choose a different rule, it must stay equally narrow and be explicitly justified in code/comments/tests
- do not mutate linked order/payment/tour state
- do not add side-effect notifications in this step

4. Response shape:
- return updated AdminHandoffRead
- preserve queue-friendly fields introduced in Step 18
- keep route layer thin
- keep transition logic in service layer
- keep repositories persistence-oriented only

5. Preserve consistency with Step 19:
- Step 19 introduced `mark-in-review`
- Step 20 should complement it narrowly, not redesign it
- do not backdoor broader workflow semantics

Очень важно:
- do not add claim/assign in this step
- do not add reopen
- do not add both close and other status mutations
- do not add operator workflow engine
- do not add notifications side effects
- do not touch public handoff creation flow
- do not change booking/payment flows

Разрешённый scope:
- one narrow handoff close mutation only
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- claim/assign
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
- покрыть protected access for `POST /admin/handoffs/{handoff_id}/close`
- покрыть successful status change
- покрыть idempotent behavior for already closed
- покрыть not-found behavior
- покрыть invalid current status handling (`open -> 400`, если выбрана рекомендованная семантика)
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed