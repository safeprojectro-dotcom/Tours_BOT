Перед кодом (кратко)
Фаза: Phase 5 / Step 16 — minimal handoff operator actions

Почему этот шаг сейчас логичен
- handoff entries уже реально создаются из private chat и Mini App
- ops queue visibility уже есть через internal read-only endpoints
- без минимальных действий оператор не может перевести заявку из “open” в рабочее состояние
- нужен не full CRM, а маленький безопасный action loop

Что уже есть
- GET /internal/ops/handoffs/open
- GET /internal/ops/waitlist/active
- token protection via OPS_QUEUE_TOKEN
- handoff.status реально используется как минимум в состоянии open
- assigned_operator_id поле уже существует у handoff/order area или рядом в модели проекта

Цель этого среза
Сделать минимальные действия только для handoff:
1. взять handoff в работу
2. при необходимости назначить operator id
3. закрыть handoff после обработки
4. не трогать waitlist actions
5. не строить UI — только internal API + tests + docs

Жёсткие границы scope
Не менять:
- booking logic
- payment logic
- expiry logic
- reconciliation
- Mini App public flow
- bot public flow
- waitlist promotion
- notification pipeline
- full auth/roles system
- отдельную admin SPA
- schema migrations, если можно без них

Что сначала нужно проанализировать
1. Какие статусы у handoff уже допустимы в модели/enum/БД
2. Можно ли использовать существующие статусы без миграции
3. Есть ли already existing repository update methods
4. Есть ли natural place для assigned_operator_id
5. Можно ли остаться в чистом internal-token API

Предпочтительный safe slice
Если в модели уже допускаются статусы кроме open:
- PATCH /internal/ops/handoffs/{id}/claim
- PATCH /internal/ops/handoffs/{id}/close

Где:
claim:
- если assigned_operator_id передан — записать его
- статус перевести в “in_review” / “claimed” / ближайший уже существующий статус
- если уже не open — вернуть конфликт / понятную ошибку

close:
- статус перевести в “closed”
- не менять связанные booking/payment сущности

Если в модели нет промежуточного статуса:
- разрешён ещё более узкий slice:
  - claim только записывает assigned_operator_id, статус остаётся open
  - close переводит в closed
Но перед кодом явно сообщить, какой вариант выбран и почему

Что сделать
A) Repository / service
Добавить минимальные методы для handoff:
- claim_handoff(...)
- close_handoff(...)
С проверками:
- handoff exists
- open-only for claim
- not already closed
- safe idempotency or explicit conflict

B) Internal API
На том же internal ops surface:
- PATCH /internal/ops/handoffs/{handoff_id}/claim
- PATCH /internal/ops/handoffs/{handoff_id}/close

Защита:
- тот же OPS_QUEUE_TOKEN
- тот же механизм Authorization: Bearer или X-Ops-Token

Request body минимальный:
claim:
- optional operator_id
close:
- optional operator_id only if это полезно для следа
Не вводить лишние поля

Response минимальный и честный:
- id
- status
- assigned_operator_id
- updated_at if already exists in model
- maybe result field if это принято в проекте

C) Правила действий
Claim:
- только для open handoff
- если уже claimed/in_review/closed — не делать silent success, а вернуть понятный конфликт или already_processed
- если operator_id не передан, claim всё равно допустим только если это логично в модели; иначе перед кодом сообщить ограничение

Close:
- закрывает handoff
- не шлёт уведомлений
- не меняет booking/waitlist/order
- closed handoff перестаёт попадать в /internal/ops/handoffs/open

D) Docs
Обязательно:
- docs/PHASE_5_STEP_16_NOTES.md
- docs/CHAT_HANDOFF.md
- при необходимости короткий блок в docs/PHASE_5_STEP_8_SMOKE_CHECK.md

Ожидаемый результат
После реализации:
- ops queue не только читается, но handoff можно забрать в работу и закрыть
- open queue становится реально обслуживаемой
- waitlist остаётся read-only
- public user flow не меняется

Ручная проверка Step 16
1. Создать новый handoff
2. GET /internal/ops/handoffs/open → заявка видна
3. PATCH claim → статус/assigned_operator_id меняется
4. Повторный claim той же заявки → конфликт или понятный already processed
5. PATCH close → заявка уходит из open queue
6. GET /internal/ops/handoffs/open → закрытая запись больше не видна
7. Публичные Mini App / bot flows не изменились

Проверки
- py_compile только затронутых файлов
- узкие unit tests для service + API
- без полного suite

Перед кодом сообщи кратко:
1. какие handoff statuses уже существуют в проекте
2. какой safe slice выбран
3. нужен ли промежуточный статус или достаточно assign + close

После кодирования отчитайся строго:
1. изменённые файлы
2. что сделано в repository/service
3. какие internal endpoints добавлены
4. как ведёт себя claim
5. как ведёт себя close
6. как проверить Step 16 вручную
7. что осталось вне scope