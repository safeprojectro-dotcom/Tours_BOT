Перед кодом (кратко)
Фаза: Phase 5 / Step 14 — waitlist MVP entry

Почему идём сюда
- booking flow уже есть
- temporary hold / expiry уже есть
- mock payment confirmed path уже есть
- support / handoff entry уже есть
- следующий обязательный recovery path: пользователь пришёл на sold out тур или места временно недоступны, но хочет оставить интерес

Что уже есть
- тур может быть sold out / seats_available=0
- released / expired holds уже возвращают места
- в проектных заметках waitlist упоминается как отдельный будущий слой
- в scope этого шага нужен только MVP entry, без полного auto-allocation / operator workflow

Цель этого среза
Сделать честный waitlist MVP:
1. если тур недоступен для обычной временной брони, пользователь может оставить заявку в лист ожидания
2. это работает из Mini App
3. при необходимости доступен простой путь и из private chat
4. система ничего не обещает автоматически, если auto-promotion ещё не реализован

Жёсткие границы scope
Не менять:
- payment core logic
- reservation expiry logic
- confirmed booking logic
- reconciliation
- support / handoff existing flow
- webhook / Railway split
- admin/operator full workflow
- auto-assignment seats from waitlist
- full notification pipeline, если его ещё нет

Разрешённый scope
- minimal waitlist create path
- minimal API route(s)
- Mini App CTA / form / success state
- private chat wording / entry, если уже есть удобный безопасный путь
- read-only visibility of “you are on waitlist”, если это можно сделать тонко
- docs
- узкие tests

Что сначала нужно проанализировать
1. Есть ли уже в коде модель / таблица / repository для waitlist
2. Есть ли уже service-level create path
3. Какие поля уже существуют и какие reason/status значения допустимы
4. Можно ли сделать шаг без миграции
5. Если без миграции нельзя — сообщить это до кодинга и предложить самый узкий safe slice

Предпочтительный safe slice
Если waitlist model/repository уже есть:
- сделать WaitlistEntryService
- POST route для создания waitlist entry
- Mini App CTA только на недоступном туре / недоступной prepare-ветке
- success message с честным текстом: “interest recorded”, без обещания auto-booking

Если waitlist model ещё нет и миграция нужна:
- сначала сообщить это
- выбрать максимально узкий вариант с минимальной миграцией
- не делать лишних доменных статусов

Что нужно сделать
A) Backend
1. Найти/добавить minimal service для waitlist entry
2. Минимально валидировать:
   - tour exists
   - tour still relevant / not archived
   - user identifiable (telegram_user_id or internal user)
   - avoid obvious duplicate active waitlist entries for same user + same tour, если это уже можно сделать безопасно
3. Возвращать честный result:
   - created
   - already_exists
   - unavailable / invalid_tour
4. Не обещать auto-promotion, если его нет

B) API
Добавить minimal Mini App route, например:
- POST /mini-app/tours/{tour_code}/waitlist
или использовать существующий стиль роутов проекта, если он уже задан

Payload минимальный:
- telegram_user_id
- optional note / optional boarding_point_id only if already natural in the model
Не усложнять без нужды

C) Mini App
1. На tour detail / prepare flow, когда тур недоступен для временной брони:
   - показать waitlist CTA вместо тупика
2. После отправки:
   - success state / snackbar / info block
   - честный текст: заявка записана, это не подтверждённая бронь
3. Если уже есть активная waitlist entry:
   - не дублировать
   - показать “already on waitlist” / аналог
4. Локализация минимум:
   - en
   - ro
   - для ru/sr/hu/it/de можно через существующий pattern/fallback, но если можно — добавить и их тоже

D) Private chat
Только если можно сделать тонко и без разрастания scope:
- для случаев недоступного тура или явного user intent дать текст:
  “This tour is currently unavailable; you can join the waitlist in Mini App”
Не строить большой отдельный chat waitlist wizard, если это утащит шаг

Ожидаемый результат
После реализации:
- на sold out / unavailable туре пользователь не упирается в тупик
- можно оставить interest/waitlist entry
- дубли не плодятся без нужды
- UI честно различает:
  - confirmed booking
  - temporary hold
  - waitlist interest
- никакой ложной автоматизации не обещается

Важные UX правила
- “waitlist” ≠ “reservation”
- “waitlist” ≠ “guaranteed seat”
- тексты должны явно говорить:
  - это запись интереса / лист ожидания
  - команда может связаться / система может использовать позже
  - место не подтверждено

Что желательно добавить в тексты
Примеры смысла:
EN:
- Join waitlist
- You are on the waitlist
- Your waitlist request was recorded
- This is not a confirmed booking

RO:
- Intră pe lista de așteptare
- Ești pe lista de așteptare
- Cererea pentru lista de așteptare a fost înregistrată
- Aceasta nu este o rezervare confirmată

Проверки
- py_compile затронутых файлов
- узкие unit tests на service / duplicate handling / API route
- ручной smoke:
  1. тур доступен → обычный reserve path как раньше
  2. тур недоступен → waitlist CTA виден
  3. submit waitlist → success
  4. повторная submit → already exists / no duplicate
  5. UI не называет это booking
- полный suite не запускать

Перед кодом сообщи кратко:
1. есть ли уже waitlist model / repository / service path
2. нужен ли migration
3. какой safe slice выбран

После кодирования отчитайся строго:
1. изменённые файлы
2. что сделано в backend/service/API
3. что сделано в Mini App UX
4. есть ли duplicate protection
5. как проверить Step 14 вручную
6. что осталось вне scope