Перед кодом (кратко)
Фаза: Phase 5 / Step 19 — cleanup / archive policy for ops-visible entities

Почему этот шаг сейчас логичен
- booking/payment/waitlist/handoff flows уже работают
- internal ops queues уже существуют
- staging и ручные тесты уже накопили много исторических записей
- без понятной cleanup/archive policy операционные списки и user-facing история со временем начинают шуметь и путать

Что уже есть
- orders с active/expired/confirmed history
- handoffs с open/in_review/closed
- waitlist с active/in_review/closed
- My bookings уже разделён на Confirmed / Active / History
- ops queues уже фильтруют active/open, но нет общей политики, что считать “архивом”, что скрывать, а что оставлять

Цель этого среза
Сделать минимальную, безопасную и честную archive/cleanup policy для сущностей, которые уже видимы в продукте и ops:
1. old/noisy history не должна мешать в основных операционных и user-facing списках
2. данные не удаляются агрессивно
3. архив — это presentation/ops policy, а не разрушение БД
4. staging становится легче тестировать и анализировать

Жёсткие границы scope
Не менять:
- booking core logic
- payment core logic
- reconciliation
- expiry logic
- waitlist logic
- handoff lifecycle
- public Telegram flow semantics
- schema migrations, если можно без них
- hard delete existing data
- real retention jobs / cron cleanup

Предпочтительный safe slice
Presentation/archive policy only:
- определить, какие записи считаются “операционно активными”
- какие считаются “историей”
- какие можно скрывать по умолчанию, но не удалять
- какие read endpoints / screens должны показывать compact view vs full history view

Что сначала нужно проанализировать
1. Где сейчас already visible history мешает больше всего:
   - My bookings
   - ops queues
   - internal read endpoints
   - maybe booking detail entry lists
2. Есть ли уже convenient filters/params в read paths
3. Можно ли обойтись query params / optional compact mode
4. Какой минимум даст заметную пользу без нового UI/SPA

Наиболее полезный safe slice
A) User-facing
Для My bookings:
- оставить текущую группировку
- добавить optional compact mode / default truncation for History:
  - например показывать только последние N history items
  - older history скрывать под “Show older history” только если это дешево по UI
или
- если не хочется UI-кнопок, хотя бы ограничить History разумным числом сверху и задокументировать policy

B) Ops-facing
Для internal ops queues:
- уже active/open only — это хорошо, не менять смысл
- но добавить optional endpoint/query for recently closed/recent history only if это полезно и дёшево
или честно оставить ops queues как active-only, а в docs зафиксировать archive policy
Главное — не раздувать шаг

C) Service policy
Определить и задокументировать:
- orders:
  - active/confirmed visible
  - old expired/released stay in history
  - default compact history policy for Mini App
- handoffs:
  - open/in_review in queue
  - closed out of queue
- waitlist:
  - active/in_review visible where needed
  - closed out of queue
- staging cleanup scripts remain separate and do not replace archive policy

Что сделать
1. Выбрать один минимальный pain-point и решить его product-safe способом.
Предпочтительно:
- My bookings history compaction
2. Если делается UI:
- не ломать existing grouping
- просто ограничить шум в History section
3. Если делается API/read parameter:
- keep backward compatibility where practical
- clearly document default behavior
4. Добавить docs:
- docs/PHASE_5_STEP_19_NOTES.md
- docs/CHAT_HANDOFF.md
- docs/PHASE_5_STEP_8_SMOKE_CHECK.md (короткий блок)

Важные правила
- archive != delete
- history != active workload
- old released holds не должны доминировать над реальными текущими бронями
- ops queue не должна превращаться в мусорный лог
- staging reset scripts остаются operational tools, а не заменой archive policy

Ожидаемый результат
После реализации:
- основные экраны и очереди выглядят чище
- исторические записи не исчезают без следа, но не мешают
- нет агрессивного удаления данных
- поведение честно задокументировано

Проверки
- py_compile затронутых файлов
- узкие unit tests, если добавляется helper / API param / grouping logic
- ручной smoke:
  1. confirmed и active bookings still visible
  2. old history no longer dominates My bookings
  3. ops queues still show only actionable items
  4. no booking/payment regressions
- полный suite не запускать

Перед кодом сообщи кратко:
1. какой exact pain-point выбран в этом шаге
2. какой safe archive/cleanup policy вводится
3. есть ли изменения только в UI/read layer или ещё в API

После кодирования отчитайся строго:
1. изменённые файлы
2. что именно изменено в cleanup/archive policy
3. как теперь ведут себя user-facing lists
4. как теперь ведут себя ops-visible lists
5. как проверить Step 19 вручную
6. что осталось вне scope