Перед кодом (кратко)
Фаза: Phase 5 / Step 17 — minimal waitlist operator actions

Почему этот шаг сейчас логичен
- handoff queue уже имеет read + action loop
- waitlist queue пока только read-only
- для операционной завершённости нужен минимальный lifecycle и для waitlist
- не нужен auto-promotion в booking, нужен только безопасный ops control

Что уже есть
- GET /internal/ops/waitlist/active
- записи waitlist создаются из Mini App
- handoff lifecycle уже есть: open -> in_review -> closed
- waitlist пока не имеет operator actions

Цель этого среза
Сделать минимальные действия только для waitlist:
1. пометить active waitlist entry как in_review / contacted / ближайший существующий безопасный статус
2. закрыть / деактивировать waitlist entry после обработки
3. убрать обработанные записи из active queue
4. не делать auto-booking
5. не трогать payment/booking core

Жёсткие границы scope
Не менять:
- booking logic
- payment logic
- expiry logic
- reconciliation
- handoff flow
- Mini App public booking flow
- auto-promotion from waitlist
- operator notifications
- full admin SPA
- schema migrations, если можно без них

Что сначала нужно проанализировать
1. Какие статусы у waitlist уже есть/допустимы в модели
2. Есть ли в БД/коде уже активный/closed/reviewed статусный паттерн
3. Можно ли обойтись строковыми статусами без миграции, как с handoff
4. Есть ли already existing repository update methods
5. Какой самый маленький безопасный lifecycle выбрать

Предпочтительный safe slice
Если waitlist.status — обычная строка:
- active
- in_review
- closed

Тогда:
- PATCH /internal/ops/waitlist/{id}/claim
- PATCH /internal/ops/waitlist/{id}/close

Если промежуточный статус не нужен:
- можно сделать только close/deactivate
Но лучше иметь intermediate status, чтобы запись уходила из active queue сразу после взятия в работу

Что сделать
A) Service / repository
Добавить minimal service, например WaitlistOpsActionService:
- claim_waitlist_entry(...)
- close_waitlist_entry(...)

Правила:
claim:
- только из active
- переводит в in_review
- при необходимости может принимать optional operator_id только если это естественно ложится в существующую модель
- если operator assignment у waitlist отсутствует в модели, НЕ добавлять его искусственно

close:
- из active или in_review -> closed
- без side effects на booking/payment
- без auto-promotion seats

Если у waitlist нет operator_id поля:
- не изобретать его
- оставить только смену статуса

B) Internal API
Добавить:
- PATCH /internal/ops/waitlist/{waitlist_id}/claim
- PATCH /internal/ops/waitlist/{waitlist_id}/close

Защита:
- тот же OPS_QUEUE_TOKEN
- тот же auth механизм, что у ops queue

Request body:
- пустой или минимальный
- только если реально нужно что-то передать
Не усложнять

Response:
- id
- status
- user_id
- tour_id
- seats_count
- created_at
- maybe result if это помогает, но кратко

C) Queue behavior
GET /internal/ops/waitlist/active должен по-прежнему возвращать только active.
После claim запись больше не должна попадать в active queue.
После close тем более не должна попадать.

D) Docs
Обязательно:
- docs/PHASE_5_STEP_17_NOTES.md
- docs/CHAT_HANDOFF.md
- при необходимости короткий блок в docs/PHASE_5_STEP_8_SMOKE_CHECK.md

Ожидаемый результат
После реализации:
- waitlist queue становится не только читаемой, но и обслуживаемой
- ops может взять waitlist interest в работу
- ops может закрыть обработанную запись
- public flow не меняется
- никакой ложной автоматической брони не появляется

Важные правила
- waitlist != booking
- claim waitlist != reserve seats
- close waitlist != notify user automatically
- не вводить скрытых side effects

Ручная проверка Step 17
1. Создать active waitlist entry
2. GET /internal/ops/waitlist/active — запись видна
3. PATCH claim — статус меняется, запись пропадает из active queue
4. Повторный claim — 409 или понятный conflict
5. PATCH close — запись переходит в closed
6. Повторный close — 409 или понятный conflict
7. Публичные Mini App flows не меняются

Проверки
- py_compile только затронутых файлов
- узкие unit tests для service + API
- без полного suite

Перед кодом сообщи кратко:
1. какие статусы waitlist уже существуют в проекте
2. какой lifecycle выбран
3. нужен ли промежуточный статус
4. есть ли operator assignment или шаг без него

После кодирования отчитайся строго:
1. изменённые файлы
2. что сделано в service/repository
3. какие internal endpoints добавлены
4. как ведёт себя claim
5. как ведёт себя close
6. как проверить Step 17 вручную
7. что осталось вне scope