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
- Phase 6 / Steps 1–4 completed:
  - protected admin foundation
  - read-only overview / tours / orders
  - list/detail/filter visibility
- Phase 6 / Step 5 completed:
  - POST /admin/tours
- Phase 6 / Step 6 completed:
  - PUT /admin/tours/{tour_id}/cover
- Phase 6 / Step 7 completed:
  - PATCH /admin/tours/{tour_id}
- Phase 6 / Step 8 completed:
  - POST /admin/tours/{tour_id}/boarding-points
- Phase 6 / Step 9 completed:
  - PATCH /admin/boarding-points/{boarding_point_id}
- Phase 6 / Step 10 completed:
  - DELETE /admin/boarding-points/{boarding_point_id}
- Phase 6 / Step 11 completed:
  - PUT /admin/tours/{tour_id}/translations/{language_code}
- Phase 6 / Step 12 completed:
  - DELETE /admin/tours/{tour_id}/translations/{language_code}
- Phase 6 / Step 13 completed:
  - PUT /admin/boarding-points/{boarding_point_id}/translations/{language_code}
- Phase 6 / Step 14 completed:
  - DELETE /admin/boarding-points/{boarding_point_id}/translations/{language_code}
- Phase 6 / Step 15 completed:
  - POST /admin/tours/{tour_id}/archive
  - POST /admin/tours/{tour_id}/unarchive
- Phase 6 / Step 16 completed:
  - read-only admin order/payment correction visibility on GET /admin/orders/{order_id}
- Phase 6 / Step 17 completed:
  - read-only admin action preview on GET /admin/orders/{order_id}
- admin read-side is established
- narrow admin write slices for tours, boarding points, and translations exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 18

Нужен только один узкий safe slice:
FIRST NARROW ADMIN HANDOFF QUEUE VISIBILITY / DETAIL SLICE

Важно:
это НЕ handoff mutation workflow.
Это только read-only admin visibility for existing handoff-related operational work.

Что именно сделать:
1. Добавить read-only admin visibility for handoff queue.
Предпочтительный узкий вариант:
   - GET /admin/handoffs
   - GET /admin/handoffs/{handoff_id}
Если detail feels too much for one slice, start with list only, but prefer list + detail if it stays narrow.

2. Цель шага:
- дать админу/operator-уровню visibility по существующим handoff records
- видеть open / in-progress / closed style operational state if already persisted
- связать handoff с source entity minimally (order / user / tour if available)
- не открывать assignment / resolution / status mutation yet

3. Что показывать в list/detail:
Только узкий, already-persisted, operationally useful набор.
Например:
- handoff id
- status
- category / reason / source if present
- created_at / updated_at
- linked order_id if present
- linked user_id if present
- linked tour_id if safely derivable/persisted
- brief summary / note / request text if already in model
- language if present
- queue-oriented indicators:
  - is_open
  - needs_attention
  - age bucket / created age only if trivial and safe
Не изобретай wide CRM/workflow layer.

4. Validation / safety rules:
- read-only only
- no mutation of handoff state
- no operator assignment
- no status transition
- no queue claiming
- no public flow changes
- if linked entities are missing, return stable read-side shapes without failing broadly

5. Response shape:
- add narrow admin read schemas
- keep route layer thin
- keep interpretation/computed queue indicators in service layer
- keep repositories persistence-oriented only

Очень важно:
- do not add handoff mutation endpoints in this step
- do not build operator workflow engine
- do not add notifications side effects
- do not widen into support chat system
- do not touch public handoff creation behavior
- do not change booking/payment flows

Разрешённый scope:
- narrow read-only handoff queue visibility
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- handoff claim/assign
- handoff status mutation
- operator workflow engine
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
- покрыть protected access for new admin handoff endpoint(s)
- покрыть successful handoff list read
- покрыть successful handoff detail read if detail included
- покрыть not-found behavior for detail if applicable
- покрыть at least one open handoff case
- покрыть at least one closed/non-open case if supported by fixtures/model
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint / endpoints
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed