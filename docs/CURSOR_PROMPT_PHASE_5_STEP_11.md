Перед кодом (кратко)
Фаза: Phase 5 / Step 11 — My bookings cleanup and UX hardening

Почему идём сюда
- Step 10 уже работает: mock payment completion доводит бронь до confirmed/paid
- в My bookings теперь одновременно видны:
  - active temporary holds
  - confirmed paid bookings
  - released/expired unpaid holds
- логика корректна, но UX пока шумный: реальные важные брони смешаны с тестовой/исторической “грязью”

Цель этого среза
Сделать экран My bookings более понятным и продуктовым, не меняя бизнес-логику бронирования/оплаты.
Нужно визуально и логически разделить:
1. активные временные hold
2. подтверждённые брони
3. история (released/expired unpaid)

Жёсткие границы scope
Не менять:
- schema / migrations
- payment logic / reconciliation
- lazy expiry
- TTL hold
- webhook / Railway split
- admin/operator flows
- waitlist
- real PSP integration

Разрешённый scope
- mini_app/app.py
- mini_app/ui_strings.py
- при необходимости тонкие facade/helper функции для UI-группировки
- docs
- узкие unit tests, если нужны

Что нужно сделать
1. Проанализировать текущий экран My bookings:
   - как сейчас формируется список
   - какие facade_state/status уже доступны
2. Реализовать безопасную UX-группировку без смены доменной модели:
   - блок Confirmed bookings
   - блок Active holds
   - блок History
3. Правила группировки:
   - confirmed/paid -> Confirmed bookings
   - active hold / awaiting payment -> Active holds
   - released / expired / unpaid cancelled_no_payment -> History
   - если блок пустой, его можно не показывать
4. Сохранить текущие карточки и кнопку Open, но сделать список читаемее:
   - confirmed сверху
   - active holds после них
   - history внизу
5. Добавить краткие заголовки/подписи секций в ui_strings
   - en + ro
6. Не ломать текущий booking detail flow
7. Обновить docs:
   - docs/PHASE_5_STEP_11_NOTES.md — новый
   - docs/PHASE_5_STEP_8_SMOKE_CHECK.md — короткий блок Step 11
   - docs/CHAT_HANDOFF.md — обновить текущую фазу

Ожидаемый результат
После реализации:
- My bookings визуально разделяет активное и архив
- confirmed booking не теряется среди released holds
- staging screen становится понятнее без изменения БД и payment lifecycle

Предпочтительная стратегия
- использовать уже существующий facade_state
- не выдумывать новые статусы
- grouping только на уровне Mini App UI / thin helper

Проверка
Сделать минимальные проверки:
- py_compile для изменённых файлов
- узкий smoke вручную:
  - увидеть confirmed booking в отдельном верхнем блоке
  - увидеть active hold отдельно
  - увидеть expired/released записи в History
- полный test suite не запускать

Перед кодом сообщи кратко:
1. по каким полям сейчас разумнее группировать
2. какой минимальный safe slice будет сделан

После кодирования отчитайся строго:
1. изменённые файлы
2. что изменено в My bookings UX
3. как работает группировка
4. что изменено в строках/локализации
5. как вручную проверить Step 11
6. что осталось вне scope