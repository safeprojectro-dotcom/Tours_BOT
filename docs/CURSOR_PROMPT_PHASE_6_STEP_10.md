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
- production migration mismatch after Step 6 was recovered successfully
- admin read-side is established
- first admin write slices for tours and boarding points exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 10

Нужен только один узкий safe slice:
FIRST NARROW BOARDING POINT DELETE-ONLY SLICE

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - DELETE /admin/boarding-points/{boarding_point_id}

2. Реализовать только delete of a single boarding point by id

3. Validation / safety rules in service layer:
   - boarding point must exist
   - delete only this boarding point
   - do not cascade into wider route/itinerary management logic
   - no tour reassignment behavior
   - keep the operation narrow and explicit

4. Response shape:
   - choose one narrow consistent pattern:
     - 204 No Content
     - or 200 with a small deleted/ok payload
   Prefer the narrower option and keep it consistent with your existing style.

5. Keep route layer thin
6. Keep business validation in service layer
7. Keep repository persistence-oriented only

Очень важно:
- do not add batch delete
- do not add route reorder/renumber logic
- do not add translations mutation
- do not widen into full itinerary management
- do not change public catalog/Mini App behavior in this step

Разрешённый scope:
- one delete endpoint only
- minimal service/repository expansion needed for delete
- focused tests

Запрещено в этом шаге:
- translations CRUD
- order/payment/handoff mutations
- content/publication features
- frontend/admin SPA expansion
- broad refactor
- public booking/payment/waitlist/handoff changes
- broader route/itinerary redesign

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли endpoint
3. перечисли schemas/services/repository changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть protected access for DELETE /admin/boarding-points/{boarding_point_id}
- покрыть successful delete
- покрыть not-found behavior
- убедиться, что удаляется только одна точка
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed