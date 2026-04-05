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
- admin read-side is established
- first admin write slice exists
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 6

Нужен только один узкий safe slice:
ATTACH COVER / MEDIA REFERENCE TO TOUR

Важно:
это НЕ полноценный upload/media management module.
Это только узкий способ привязать media reference / cover reference к туру.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint for tour media reference, narrow scope only.
Предпочтительный вариант:
   - POST /admin/tours/{tour_id}/cover
   или
   - PUT /admin/tours/{tour_id}/cover
Выбери один вариант и используй его последовательно.

2. Реализовать только minimal cover/media reference attach:
   - reference string / media_path / media_url / storage key
   - один cover reference per tour
   - no gallery management
   - no upload binary handling unless the existing architecture already safely supports it
   - no external storage integration wave in this step

3. Если текущая schema/model не имеет явного поля под cover/media reference:
   - add the narrowest safe persistence change needed
   - migration only if truly necessary
   - do not over-model gallery/media library now

4. Add admin schema(s) for:
   - request payload
   - returned admin tour read/detail DTO with cover/media reference visible

5. Validation rules:
   - tour must exist
   - empty/blank media reference should be rejected as safe client error
   - do not allow this step to become “full media manager”

6. Keep route layer thin
7. Keep business validation in service layer
8. Keep repository persistence-oriented only

Очень важно:
- do not implement real file upload infrastructure in this step unless already trivial and existing
- do not add multi-image gallery management
- do not add translation-bound media
- do not add delete/replace history/audit wave beyond what is minimally necessary
- do not change public catalog logic except exposing the stored cover/media reference in existing admin read DTOs if appropriate
- do not widen into full tour update CRUD

Разрешённый scope:
- one narrow media/cover attach endpoint
- minimal persistence support for one cover/media reference
- minimal read DTO extension if needed
- focused tests

Запрещено в этом шаге:
- full upload subsystem
- gallery CRUD
- full tour update/delete/archive
- translations CRUD
- boarding points CRUD
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
3. перечисли schemas/services/repository/model changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть protected access for new cover/media endpoint
- покрыть successful attach/update of cover/media reference
- покрыть not-found behavior
- покрыть blank/invalid payload rejection
- если поле стало видно в admin detail read DTO — покрыть это
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed