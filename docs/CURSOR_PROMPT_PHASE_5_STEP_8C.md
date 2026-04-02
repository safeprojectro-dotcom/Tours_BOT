Перед кодом (кратко)
Фаза: Phase 5 / Step 8C staging data hygiene
Причина: после Step 8B Mini App и bot flow в целом работоспособны, но основной smoke-flow снова невоспроизводим, потому что TEST_BELGRADE_001 загрязнён staging test-data:
- в orders/payments накопились активные записи по этому туру
- тур ушёл в sold out / seats_available=0
- prepare для TEST_BELGRADE_001 возвращает недоступность не из-за UI-багов, а из-за состояния данных
- это мешает объективно тестировать catalog → detail → prepare → booking → payment flow

Что важно
- это НЕ redesign reservation/business logic
- это НЕ шаг по product rules
- это staging data hygiene / reproducibility slice
- бизнес-логика hold/payment/reconciliation сейчас не меняется

Цель этого среза
Надёжно восстановить TEST_BELGRADE_001 в чистое smoke состояние и зафиксировать понятный операционный сценарий reset → smoke → reset.

Жёсткие границы scope
Не менять:
- booking/payment core rules
- reservation lifecycle semantics
- webhook
- Mini App architecture
- DB schema / migrations
- Step 9+
- UI beyond what is needed for smoke reproducibility

Разрешённый scope
- scripts/reset_test_belgrade_tour_state.py
- scripts/seed_test_belgrade_tour.py
- docs for staging reset / smoke reproducibility
- minimal audit/validation helpers if needed
- optional tiny backend-safe fixes only if reset currently misses tour-related rows for TEST_BELGRADE_001

Что нужно сделать
1. Проверить, почему reset сейчас недостаточно очищает TEST_BELGRADE_001:
   - orders
   - payments
   - notification_outbox
   - waitlist
   - другие tour-related staging artifacts, если они влияют на availability
2. Сделать reset действительно воспроизводимым:
   после reset должно быть:
   - tour.status = open_for_sale
   - seats_available = seats_total
   - prepare снова доступен для ручного smoke-test
3. Если нужно, усилить seed:
   - чтобы после seed test tour имел предсказуемое стартовое состояние
   - без накопленного мусора от предыдущих прогонов
4. Добавить простой способ проверки reset результата:
   либо понятный stdout скрипта,
   либо отдельный validation helper,
   либо документированный checklist
5. Обновить документацию:
   - docs/PHASE_5_STEP_8_SMOKE_CHECK.md
   - docs/PHASE_5_STEP_8B_NOTES.md или новый docs/PHASE_5_STEP_8C_NOTES.md
   Нужно явно зафиксировать:
   - TEST_BELGRADE_001 — staging-only test tour
   - перед повторным full smoke может требоваться reset
   - My bookings показывает текущего пользователя, а не все orders в DB
   - prepare-unavailable при sold out из-за test-data не трактовать как UI defect

Ожидаемый результат
После reset:
- TEST_BELGRADE_001 снова виден как open_for_sale
- seats_available восстановлены
- detail открывается
- prepare доступен
- можно создать ровно одну новую test reservation и проверить My bookings/payment flow
- staging flow снова воспроизводим

Вероятные файлы в scope
- scripts/reset_test_belgrade_tour_state.py
- scripts/seed_test_belgrade_tour.py
- optional tiny repo/service/helper files only if reset needs them
- docs/PHASE_5_STEP_8_SMOKE_CHECK.md
- optional docs/PHASE_5_STEP_8C_NOTES.md

Очень важно
- не пытаться сейчас исправлять бизнес-модель бронирования
- не менять product rules из-за staging data problem
- fixes должны касаться только TEST_BELGRADE_001 и его test artifacts
- результат должен быть простым для ручного использования из Windows/PowerShell

Перед кодом сообщи кратко:
1. почему prepare сейчас недоступен
2. что именно мешает reset быть надёжным
3. какой минимальный safe fix будет сделан

После кодирования отчитайся строго в формате:
1. изменённые файлы
2. как теперь работает reset TEST_BELGRADE_001
3. как проверить, что тур снова пригоден для smoke
4. обновлённые smoke-test steps
5. что осталось вне scope