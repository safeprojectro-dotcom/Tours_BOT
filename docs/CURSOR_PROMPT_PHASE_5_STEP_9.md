Перед кодом (кратко)
Фаза: Phase 5 / Step 9 — reservation/payment lifecycle stabilization
Почему идём сюда:
- staging smoke-flow уже подтверждён end-to-end: catalog → detail → prepare → booking hold → payment entry
- инфраструктура, webhook, Mini App UI и staging reset уже стабилизированы
- следующий реальный продуктовый риск теперь не UI, а жизненный цикл hold/payment:
  1. как долго hold живёт
  2. когда и как он истекает
  3. как места возвращаются в продажу
  4. как это отражается в My bookings / booking detail / payment page

Что уже известно
- temporary reservation / awaiting_payment уже существуют
- reservation_expires_at уже существует
- orders / payments уже создаются
- seats_available уменьшается при hold
- reset script подтверждает, что загрязнённые staging data могут блокировать prepare
- не нужно заново проектировать систему с нуля — нужно аккуратно стабилизировать уже существующий lifecycle

Цель этого среза
Сделать lifecycle hold/payment предсказуемым и пригодным для staging и будущего production:
1. expired holds должны освобождать места
2. order / payment statuses должны быть согласованы
3. user должен видеть понятный статус в Mini App
4. false sold out из-за старых hold не должен сохраняться бесконечно

Жёсткие границы scope
Не менять:
- Railway deployment model
- Telegram webhook flow
- Mini App service split
- core catalog/filter UX
- schema migrations, если можно избежать
- сложные operator/admin workflows
- реальную интеграцию платёжного провайдера beyond current mock/payment-entry flow

Разрешённый scope
- services / repositories / helpers, связанные с hold expiry / release
- order/payment status transition logic
- lightweight cleanup/release path for expired holds
- Mini App status wording / UX for expired vs awaiting payment vs confirmed
- docs for lifecycle and smoke-test
- minimal DB changes only if absolutely necessary and justified

Что нужно сделать
1. Проанализировать текущую lifecycle-логику:
   - где создаётся temporary reservation
   - где вычисляется reservation_expires_at
   - где сейчас происходит (или не происходит) release expired holds
   - как влияет expired hold на seats_available
2. Реализовать минимально безопасный механизм истечения hold:
   - если hold истёк и оплата не подтверждена, бронь больше не должна блокировать места
   - seats_available должны возвращаться корректно
   - order должен переходить в понятное released / expired / cancelled-not-paid состояние (использовать существующие статусы/поля, если возможно)
3. Согласовать payment lifecycle:
   - awaiting_payment пока hold активен
   - после expiry больше не должно выглядеть как будто бронь всё ещё валидна
   - My bookings / booking detail / payment screen должны показывать понятное состояние
4. Не делать тяжёлую фоновую инфраструктуру, если для этого среза можно безопасно использовать:
   - lazy release при чтении / перед critical actions
   - service-level cleanup
   - или маленький operational helper / script
   Но решение должно быть объяснимым и staging-safe
5. Обновить Mini App UX текстовку:
   - awaiting payment
   - payment deadline
   - expired / released
   - seats no longer held
   - what user should do next
6. Обновить документацию:
   - новый docs/PHASE_5_STEP_9_NOTES.md
   - при необходимости update docs/PHASE_5_STEP_8_SMOKE_CHECK.md
   Нужно зафиксировать:
   - lifecycle статусов
   - что происходит при expiry
   - как это влияет на seats_available
   - как тестировать flow вручную

Ожидаемый результат
После реализации:
- hold не живёт бесконечно
- истёкшие брони перестают блокировать места
- false sold out из-за старых awaiting_payment reservations уменьшается / исчезает
- Mini App показывает понятный booking/payment status
- staging можно тестировать без ручного reset после каждого старого истёкшего hold, либо с сильно меньшей зависимостью от reset

Предпочтительная стратегия
- сначала использовать существующие поля и статусы
- избегать новых сущностей без крайней необходимости
- минимальный safe slice лучше большого redesign
- если полноценный background cleanup пока избыточен, допустим lazy-expiry approach, но с чёткой документацией

Вероятные файлы в scope
- app/services/... temporary reservation / payment / booking lifecycle
- app/repositories/... orders / tours / payments
- mini_app/app.py
- mini_app/ui_strings.py
- scripts/... optional lifecycle helper
- docs/PHASE_5_STEP_9_NOTES.md

Очень важно
- не ломать текущий working smoke-flow
- не переписывать весь booking/payment subsystem
- не маскировать проблему reset script’ом там, где нужна нормальная expiry logic
- changes должны быть понятны, ограничены и обратимы

Перед кодом сообщи кратко:
1. как сейчас живёт hold lifecycle
2. где именно отсутствует или неполон expiry/release
3. какой минимальный safe slice будет сделан

После кодирования отчитайся строго в формате:
1. изменённые файлы
2. что изменено в hold expiry / release logic
3. что изменено в order/payment status handling
4. что изменено в Mini App UX/status texts
5. как теперь тестировать lifecycle вручную
6. что осталось вне scope