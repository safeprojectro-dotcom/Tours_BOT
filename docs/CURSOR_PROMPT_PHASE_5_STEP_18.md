Перед кодом (кратко)
Фаза: Phase 5 / Step 18 — waitlist user visibility polish

Почему этот шаг сейчас логичен
- ops lifecycle для waitlist уже есть: active -> in_review -> closed
- но user-facing логика Mini App всё ещё считает “on waitlist” только status=active
- из-за этого после ops claim пользователь может выглядеть так, будто его заявка исчезла
- нужен product polish: пользователь должен видеть, что waitlist request всё ещё существует, пока она не закрыта

Что уже есть
- waitlist create path из Mini App
- GET /mini-app/tours/{tour_code}/waitlist-status?telegram_user_id=...
- POST /mini-app/tours/{tour_code}/waitlist
- internal ops actions:
  - PATCH /internal/ops/waitlist/{id}/claim
  - PATCH /internal/ops/waitlist/{id}/close
- waitlist statuses: active, in_review, closed
- MiniAppWaitlistService сейчас считает “on waitlist” только active

Цель этого среза
Исправить user-facing видимость waitlist без изменения core booking/payment:
1. если waitlist entry уже claimed/in_review, пользователь всё ещё видит, что его интерес записан
2. если запись closed, UI больше не показывает “you are on waitlist”
3. тексты различают:
   - active waitlist
   - in review / being reviewed
   - closed / no longer active
4. waitlist по-прежнему не называется booking и не обещает место

Жёсткие границы scope
Не менять:
- booking logic
- payment logic
- expiry logic
- reconciliation
- ops queue/action endpoints
- auto-promotion to booking
- notifications
- admin UI
- migrations, если можно без них

Что сначала нужно проанализировать
1. Где именно сейчас MiniAppWaitlistService определяет on_waitlist / eligible
2. Возвращает ли current status route достаточно данных, или нужен маленький response extension
3. Можно ли расширить waitlist-status без ломки текущего UI/API
4. Какие статусы пользователь должен видеть как “request still exists”
5. Какие тексты нужны для en/ro и как fallback будет работать для других языков

Предпочтительный safe slice
Лучший вариант:
- расширить GET /mini-app/tours/{tour_code}/waitlist-status
- отдавать не только:
  - eligible
  - on_waitlist
но и:
  - waitlist_status: null | active | in_review | closed
  - maybe user_message_key only if это уже принято, но предпочтительно без этого
- Mini App branch строить по status, а не только по boolean

Предпочтительная user-facing семантика
- active:
  “You are on the waitlist.”
  “This is not a confirmed booking.”
- in_review:
  “Your waitlist request is being reviewed.”
  “This is still not a confirmed booking.”
- closed:
  не показывать как active waitlist
  можно показать нейтральное сообщение только если это действительно полезно, но не обязательно
- eligible:
  если seats_available == 0 и статуса нет -> можно Join waitlist
- если seats появились:
  можно не тащить сложную автоматическую подсказку; не менять этот продуктовый смысл в этом шаге

Что сделать
A) Backend / service
Обновить MiniAppWaitlistService / status read path так, чтобы для пользователя различались:
- no entry
- active
- in_review
- closed
Важно:
- boolean on_waitlist должен быть true как минимум для active и in_review, если это не ломает совместимость
или
- если нужен более честный контракт, оставить on_waitlist как derived from status и явно задокументировать
Главное — Mini App должен перестать “терять” заявку после claim

B) API schema
Обновить schema ответа waitlist-status:
- eligible: bool
- on_waitlist: bool
- waitlist_status: Optional[str]
Если уместно:
- waitlist_entry_id: Optional[int]
Но не раздувать лишним

C) Mini App UX
На sold out туре:
1. если нет записи и eligible=true:
   - Join waitlist
2. если status=active:
   - блок “You are on the waitlist”
3. если status=in_review:
   - блок “Your waitlist request is being reviewed”
   - без второй кнопки Join
4. если status=closed:
   - не показывать as active
   - можно показать нейтральное info, но только если это реально улучшает UX
5. тексты должны явно говорить:
   - not a booking
   - not a guaranteed seat

D) Strings / localization
Добавить или обновить waitlist UI strings минимум для:
- en
- ro
Для ru/sr/hu/it/de допустим fallback через en, но если безопасно и компактно — можно добавить сразу

Предлагаемый смысл ключей
- waitlist_active_title
- waitlist_active_body
- waitlist_in_review_title
- waitlist_in_review_body
- waitlist_closed_body (optional)
- waitlist_not_a_booking_note (только если реально нужен отдельный ключ)

Не дублировать тексты, если это можно выразить существующими строками

E) Docs
Обязательно:
- docs/PHASE_5_STEP_18_NOTES.md
- docs/CHAT_HANDOFF.md
- при необходимости короткий блок в docs/PHASE_5_STEP_8_SMOKE_CHECK.md

Ожидаемый результат
После реализации:
- waitlist entry не “исчезает” для пользователя сразу после ops claim
- пользователь видит разницу между active и in_review
- closed entry больше не выглядит как действующая
- waitlist по-прежнему не путается с booking

Ручная проверка Step 18
1. Нет waitlist, sold out тур -> виден Join waitlist
2. Submit -> status active, UI показывает “on waitlist”
3. Ops claim entry -> status in_review, UI после refresh показывает “being reviewed”
4. Ops close entry -> waitlist больше не показывается как active/in review
5. Public booking/payment flows не изменились

Проверки
- py_compile только затронутых файлов
- узкие unit tests для waitlist status service/API/UI branching if applicable
- без полного suite

Перед кодом сообщи кратко:
1. как сейчас определяется on_waitlist
2. какой API contract выбран
3. будет ли on_waitlist true для active + in_review
4. какие user-facing states показываются

После кодирования отчитайся строго:
1. изменённые файлы
2. что изменено в waitlist status service/API
3. что изменено в Mini App UX
4. как теперь трактуются active / in_review / closed
5. как проверить Step 18 вручную
6. что осталось вне scope