Перед кодом (кратко)
Фаза: Phase 5 / Step 12 — payment edge cases and retry UX

Почему идём сюда
- success path уже работает: hold -> payment -> confirmed
- My bookings уже разделён на Confirmed / Active holds / History
- теперь нужно закрыть UX на краях payment flow, чтобы staging был продуктово устойчивым, а не только happy-path

Что именно нужно улучшить
Нужно обработать и визуально прояснить следующие сценарии:
1. hold expired before payment completion
2. mock payment completion disabled on server
3. пользователь повторно открывает booking detail/payment screen после release/expiry
4. retry path: если бронь ещё active hold, пользователь должен понимать, можно ли ещё оплатить
5. если бронь уже released/expired, UI не должен вести в ложный payment action

Жёсткие границы scope
Не менять:
- schema / migrations
- webhook / Railway split
- real PSP integration
- waitlist
- admin/operator flows
- booking business rules
- current success reconciliation path

Разрешённый scope
- mini_app/app.py
- mini_app/ui_strings.py
- тонкие helper/facade presentation functions при необходимости
- docs
- узкие unit tests

Минимальный безопасный срез
1. В booking detail и payment screen явно различать:
   - confirmed
   - active hold
   - released/expired
2. Для released/expired:
   - не показывать CTA оплаты
   - показать понятное сообщение, что hold освобождён и нужно начать заново из каталога
3. Для active hold:
   - CTA оплаты остаётся
   - при повторном входе текст должен ясно говорить, что бронь ещё активна до дедлайна
4. Если mock payment completion disabled:
   - показывать понятное пользовательское сообщение, а не просто технический snackbar
5. Обновить строки en + ro
6. Обновить docs и CHAT_HANDOFF

Ожидаемый результат
- пользователь не попадает в тупик на expired/released booking
- UI не предлагает оплату там, где платить уже нельзя
- retry path для active hold остаётся понятным
- success path не ломается

Предпочтительный подход
- опираться на уже существующие facade_state / booking detail state
- не добавлять новых доменных статусов
- делать это как presentation/UX hardening

Проверки
- py_compile изменённых файлов
- узкий ручной smoke:
  1. active hold -> payment screen shows pay CTA
  2. confirmed booking -> no pay CTA
  3. released/expired booking -> no pay CTA, clear restart message
  4. mock disabled -> понятное сообщение
- полный suite не запускать

Перед кодом сообщи кратко:
1. какие состояния UI уже есть и как ты их используешь
2. какой safe slice делаешь

После кодирования отчитайся строго:
1. изменённые файлы
2. что изменено в booking detail/payment UX
3. как теперь ведут себя active / confirmed / released bookings
4. что изменено в локализации
5. как проверить Step 12 вручную
6. что осталось вне scope