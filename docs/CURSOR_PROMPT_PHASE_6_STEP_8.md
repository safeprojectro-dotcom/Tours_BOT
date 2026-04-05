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
  - overview / tours list / orders list
- Phase 6 / Step 2 completed:
  - order detail
- Phase 6 / Step 3 completed:
  - tour detail
- Phase 6 / Step 4 completed:
  - read-only filtering expansion for tours/orders
- Phase 6 / Step 5 completed:
  - POST /admin/tours (create-only core tour record)
- Phase 6 / Step 6 completed:
  - PUT /admin/tours/{tour_id}/cover (one cover_media_reference)
- production migration mismatch after Step 6 was recovered successfully
- admin read-side is established
- first admin write slices exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 7

Нужен только один узкий safe slice:
FIRST NARROW UPDATE-CORE-TOUR-FIELDS-ONLY SLICE

Что именно сделать:
1. Добавить только один protected admin mutation endpoint for updating core tour fields.
Предпочтительный вариант:
   - PATCH /admin/tours/{tour_id}

2. Разрешить обновлять только core fields already established in create flow:
   - title_default
   - short_description_default
   - full_description_default
   - duration_days
   - departure_datetime
   - return_datetime
   - base_price
   - currency
   - seats_total
   - sales_deadline
   - status
   - guaranteed_flag

3. Не разрешать в этом шаге:
   - code change
   - translations mutation
   - boarding points mutation
   - cover/media mutation through this endpoint
   - delete/archive semantics

4. Validation rules in service layer:
   - tour must exist
   - return_datetime > departure_datetime
   - if sales_deadline is set, it must remain safely before departure_datetime
   - seats_total validation must be safe and coherent
   - any seats_available adjustment must be handled conservatively and safely

Очень важно для seats:
- do not introduce unsafe seat mutation logic
- if changing seats_total could conflict with existing reserved/confirmed occupancy assumptions, choose the narrowest safe rule
- prefer conservative validation over risky automatic recalculation
- document the chosen rule in code/comments/tests

5. Keep route layer thin
6. Keep business validation in service layer
7. Keep repository persistence-oriented only

Разрешённый scope:
- one narrow core update endpoint
- update schema(s)
- minimal service/repository expansion needed for update
- focused tests

Запрещено в этом шаге:
- code mutation
- delete/archive endpoints
- translations CRUD
- boarding points CRUD
- cover/media endpoint redesign
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
- покрыть protected access for PATCH /admin/tours/{tour_id}
- покрыть successful update of allowed fields
- покрыть not-found behavior
- покрыть validation failures
- покрыть conservative seats_total handling rule
- убедиться, что code cannot be changed through this endpoint
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed