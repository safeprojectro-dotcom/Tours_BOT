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
- admin read-side is established
- first admin write slices for tours and boarding points exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 11

Нужен только один узкий safe slice:
FIRST NARROW TOUR TRANSLATIONS CREATE/UPDATE-ONLY SLICE

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - PUT /admin/tours/{tour_id}/translations/{language_code}
или
   - PATCH /admin/tours/{tour_id}/translations/{language_code}
Выбери один вариант и используй его последовательно.

2. Разрешить создать или обновить перевод для одного языка за один запрос.

3. Поля перевода:
   - title
   - short_description
   - full_description
   - program_text
   - included_text
   - excluded_text

4. Validation rules in service layer:
   - tour must exist
   - language_code must be allowed/safe according to current project rules
   - text fields may be optional/partial depending on chosen endpoint semantics
   - blank handling must be explicit and safe
   - one request affects only one language translation

5. Return one narrow admin-facing response shape:
   - either updated translation object
   - or updated AdminTourDetailRead
Choose one consistent shape and keep it narrow.

6. Keep route layer thin
7. Keep business validation in service layer
8. Keep repository persistence-oriented only

Очень важно:
- do not open bulk translation management
- do not add translation delete in this step
- do not add boarding point translations in this step
- do not change public catalog/Mini App behavior in this step
- do not widen into content publication workflow

Разрешённый scope:
- one create/update endpoint only
- translation schema(s)
- minimal service/repository expansion needed for create/update
- focused tests

Запрещено в этом шаге:
- translation delete
- boarding point translations
- order/payment/handoff mutations
- content publication workflow
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
- покрыть protected access for chosen translation endpoint
- покрыть successful create/update
- покрыть tour not found
- покрыть invalid/unsupported language handling if applicable
- покрыть safe validation behavior for blank payload/text cases
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed