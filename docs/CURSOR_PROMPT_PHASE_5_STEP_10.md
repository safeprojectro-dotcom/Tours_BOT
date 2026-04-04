Перед кодом (кратко)
Фаза: Phase 5 / Step 10 — booking confirmation and payment outcome flow

Почему идём сюда
- staging smoke-flow уже проходит end-to-end до temporary reservation / payment entry
- hold TTL уже configurable через TEMP_RESERVATION_TTL_MINUTES
- lazy expiry уже освобождает места по истечении hold
- следующий реальный продуктовый gap теперь не в инфраструктуре, а в результате оплаты:
  1. что считается успешной оплатой
  2. как бронь становится подтверждённой
  3. как пользователь видит итог в Mini App
  4. как отличить awaiting payment / paid / released / expired / failed

Цель этого среза
Сделать предсказуемый post-payment outcome flow на текущем mockpay/payment-entry сценарии, без интеграции реального провайдера.
Нужен маленький, безопасный, staging-friendly шаг:
- у payment entry должен появиться понятный outcome
- confirmed booking должен отражаться в БД и Mini App
- пользователь должен видеть ясный итог и следующий шаг

Жёсткие границы scope
Не менять:
- Railway split / webhook / Mini App deployment
- schema / migrations, если можно избежать
- реального внешнего платёжного провайдера
- admin/operator flows
- waitlist/business expansion
- полную переработку booking domain
- hold TTL / lazy expiry semantics, кроме минимально необходимой увязки с payment outcome

Разрешённый scope
- services/repositories вокруг payment entry / booking confirmation
- mockpay outcome path
- Mini App payment / booking detail / my bookings UX
- docs / smoke-test
- минимальные вспомогательные функции/маршруты в рамках текущего mock flow

Что нужно сделать
1. Проанализировать текущий mock payment flow:
   - где создаётся payment entry
   - как сейчас выглядит status awaiting_payment
   - есть ли уже сервис/точка, где payment можно перевести в success/failure
   - как сейчас booking должен становиться confirmed (или этого ещё нет)
2. Реализовать минимальный safe mock outcome flow:
   - для staging/ручного теста должна быть возможность завершить mock payment успешно
   - при success:
     - payment status становится success/paid (использовать существующие статусы, если есть)
     - order перестаёт быть temporary hold и становится подтверждённой бронью
     - confirmed booking больше не должен release-иться lazy expiry
     - seats остаются занятыми окончательно
   - при failure / cancel (если безопасно вписывается в slice):
     - payment отражает неуспех
     - hold остаётся только пока не истёк, или освобождается по текущим правилам, если это уже есть
3. Mini App UX:
   - payment screen должен показывать понятный outcome
   - booking detail должен отличать:
     - awaiting payment
     - confirmed / paid
     - expired / released
     - failed / cancelled payment (если делается в этом slice)
   - My bookings должен показывать confirmed booking отдельно от temporary hold
4. Сохранить текущую простоту:
   - это mock/staging-safe flow
   - не нужен настоящий PSP
   - не нужен тяжёлый background processing
5. Обновить документацию:
   - docs/PHASE_5_STEP_10_NOTES.md — новый файл
   - update docs/PHASE_5_STEP_8_SMOKE_CHECK.md новым блоком Step 10
   - при необходимости короткая строка в docs/CHAT_HANDOFF.md

Ожидаемый результат
После реализации:
- пользователь может пройти не только до awaiting_payment, но и до понятного success outcome
- confirmed booking виден в My bookings и booking detail
- confirmed booking больше не выглядит как временная бронь
- seats после confirmed booking не возвращаются lazy expiry
- staging можно тестировать без ручной имитации “догадайся, что оплата успешна”

Предпочтительная стратегия
- использовать существующие поля/статусы максимально
- если есть mockpay service/placeholder — расширить его
- если нужен минимальный mock action/button для success outcome, сделать его только для текущего staging flow и явно задокументировать
- маленький safe slice лучше большого redesign

Очень важно
- не ломать текущий working flow temporary reservation → payment entry
- не переписывать всю payment architecture
- не добавлять лишние сущности без крайней необходимости
- если success/failure делают только success path в этом срезе — это допустимо, но надо честно указать в отчёте

Вероятные файлы в scope
- app/services/... payment entry / booking / reservation lifecycle
- app/repositories/... orders / payments
- mini_app/app.py
- mini_app/ui_strings.py
- docs/PHASE_5_STEP_10_NOTES.md
- docs/PHASE_5_STEP_8_SMOKE_CHECK.md
- возможно tests/unit/... around booking/payment services

Проверка
Сделать минимальные проверки:
- py_compile для изменённых файлов
- узкие unit tests по payment/booking outcome, если это уместно
- не запускать полный repo-wide test suite

Перед кодом сообщи кратко:
1. как сейчас заканчивается mock payment flow
2. где отсутствует confirmed booking outcome
3. какой минимальный safe slice будет сделан

После кодирования отчитайся строго в формате:
1. изменённые файлы
2. что изменено в payment outcome flow
3. что изменено в order/payment status handling
4. что изменено в Mini App UX/status texts
5. как теперь тестировать Step 10 вручную
6. что осталось вне scope