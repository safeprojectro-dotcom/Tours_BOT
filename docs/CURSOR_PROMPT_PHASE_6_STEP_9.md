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
- Phase 6 / Step 1 completed:
  - protected admin foundation
  - read-only overview / tours / orders
- Phase 6 / Step 2 completed:
  - read-only admin order detail
- Phase 6 / Step 3 completed:
  - read-only admin tour detail
- Phase 6 / Step 4 completed:
  - read-only filtering expansion for tours/orders
- Phase 6 / Step 5 completed:
  - POST /admin/tours
- Phase 6 / Step 6 completed:
  - PUT /admin/tours/{tour_id}/cover
- Phase 6 / Step 7 completed:
  - PATCH /admin/tours/{tour_id}
- Phase 6 / Step 8 completed:
  - POST /admin/tours/{tour_id}/boarding-points
- production migration mismatch after Step 6 was recovered successfully
- admin read-side is established
- first admin write slices for tours and boarding point create exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 9

Нужен только один узкий safe slice:
FIRST NARROW BOARDING POINT UPDATE-ONLY SLICE

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - PATCH /admin/boarding-points/{boarding_point_id}

2. Добавить schema(s) для partial update boarding point

3. Разрешить обновлять только core fields already established in create flow:
   - city
   - address
   - time
   - notes

4. Validation rules in service layer:
   - boarding point must exist
   - required text fields must not become blank after trim
   - time field must be validated according to current model type
   - do not allow reassignment to another tour in this step

5. Return one narrow admin-facing response shape:
   - either updated boarding point summary
   - or updated AdminTourDetailRead
Choose one consistent shape and keep it narrow.

6. Keep route layer thin
7. Keep business validation in service layer
8. Keep repository persistence-oriented only

Очень важно:
- do not add boarding point delete in this step
- do not add translations for boarding points in this step
- do not widen into full route/itinerary management
- do not change public catalog/Mini App behavior in this step
- do not add tour reassignment for a boarding point

Разрешённый scope:
- one update endpoint only
- partial update schema(s)
- minimal service/repository expansion needed for update
- focused tests

Запрещено в этом шаге:
- boarding point delete
- translations CRUD
- order/payment/handoff mutations
- content/publication features
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
2. перечисли endpoint
3. перечисли schemas/services/repository changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть protected access for PATCH /admin/boarding-points/{boarding_point_id}
- покрыть successful update
- покрыть not-found behavior
- покрыть validation failures for blank required fields
- убедиться, что tour reassignment is not allowed / not in scope
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed