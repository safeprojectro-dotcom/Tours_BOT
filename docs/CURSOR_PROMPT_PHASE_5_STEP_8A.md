Перед кодом (кратко)
Фаза: Phase 5 / Step 8A stabilization
Причина: после Step 8 staging flow в целом жив, но утренний smoke-test выявил 3 проблемы:
1. в мобильном Telegram WebView каталог Mini App не даёт нормально прокрутить экран вниз до View details
2. команды /bookings, /help, /contact в private chat фактически перехватываются языковым flow и ведут на выбор языка вместо своих ответов
3. prepare для TEST_BELGRADE_001 показывает “tour is not available for reservation preparation”, потому что тур ушёл в sold out / seats_available=0 из-за накопленных тестовых hold/booking данных

Что уже ясно
- инфраструктура исправна: Railway API, webhook, Mini App UI, DB
- это не новый инфраструктурный шаг
- это stabilization / bugfix slice после Step 8
- booking/payment бизнес-правила менять не нужно

Цель этого среза
Сделать staging smoke-test снова воспроизводимым и понятным:
1. на мобильном устройстве каталог Mini App должен скроллиться
2. /bookings, /help, /contact должны реально работать как команды, а не попадать в language picker
3. TEST_BELGRADE_001 должен быть безопасно возвращаем в “available for reservation preparation” для повторного ручного теста

Жёсткие границы scope
Не менять:
- booking/payment core business rules
- webhook flow
- Railway deploy model
- DB schema / migrations
- Step 9+
- provider/admin/handoff/waitlist scope

Разрешённый scope
- Mini App layout/scroll fix
- command routing / handler ordering / language-guard bypass for explicit commands
- staging test data reset utility for TEST_BELGRADE_001
- docs / smoke checklist update

Нужно сделать
1. Проанализировать Mini App layout и исправить мобильный scroll:
   - каталог должен прокручиваться в Telegram mobile WebView
   - карточка тура и View details должны быть достижимы на телефоне
   - fix должен быть минимальным и не ломать desktop
2. Проанализировать private chat command routing:
   - /bookings
   - /help
   - /contact
   Сейчас они уходят в выбор языка.
   Нужно сделать так, чтобы явные slash-команды обслуживались корректно даже если language onboarding ещё не завершён, либо чтобы language requirement не перехватывал эти конкретные команды.
3. Не ломая language flow, сохранить ожидаемое поведение:
   - если пользователь реально вызывает /language, picker должен работать
   - если пользователь не имеет языка, но вызывает /help или /contact, он должен получить полезный ответ, а не только picker
4. Добавить безопасный staging reset для TEST_BELGRADE_001:
   - либо через отдельный reset script
   - либо через расширение существующих test-data scripts
   Нужно снять накопленные временные holds / bookings / related payment-entry artifacts только для этого тестового тура, чтобы он снова был доступен для ручного prepare smoke-test.
5. Обновить документацию smoke-test:
   - что делать, если тур sold out из-за старых тестовых броней
   - как восстановить чистое состояние тестового тура

Ожидаемый результат
После фикса:
- на телефоне Mini App catalog скроллится
- View details можно нажать
- /bookings, /help, /contact отвечают по смыслу
- TEST_BELGRADE_001 снова доступен для reservation preparation
- staging smoke-test снова воспроизводим end-to-end

Вероятные файлы в scope
- mini_app/app.py
- mini_app/... layout helpers if present
- app/bot/handlers/private_entry.py
- app/bot/... middleware/router ordering files if needed
- scripts/seed_test_belgrade_tour.py
- scripts/delete_test_belgrade_tour.py
- optional new script like scripts/reset_test_belgrade_tour_state.py
- docs/PHASE_5_STEP_8_SMOKE_CHECK.md
- optional new docs note for staging test data reset

Очень важно
- не делать большой refactor
- не менять реальные product rules ради теста
- reset должен затрагивать только TEST_BELGRADE_001 и его связанные test artifacts
- фикс slash-команд должен быть аккуратным и предсказуемым
- Mini App scroll fix должен быть именно mobile-safe, а не случайным cosmetic tweak

Перед кодом сообщи кратко:
1. какие 3 проблемы подтверждены
2. какой минимальный stabilization slice будет сделан
3. почему он безопасен

После кодирования отчитайся строго в формате:
1. изменённые файлы
2. что исправлено в mobile Mini App scroll
3. что исправлено в command routing
4. как теперь reset/test-data cleanup работает для TEST_BELGRADE_001
5. обновлённые smoke-test steps
6. что осталось вне scope