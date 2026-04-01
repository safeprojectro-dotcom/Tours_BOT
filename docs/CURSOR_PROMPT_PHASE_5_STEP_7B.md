Перед кодом
Фаза: Phase 5 / промежуточный Step 7B
Шаг: перевести нового Telegram-бота на Railway webhook и убрать зависимость от локального polling, не меняя продуктовую логику Mini App / booking / payment.
Причина: сейчас staging работает в смешанном режиме — backend API и Mini App UI уже живут на Railway, но Telegram-бот фактически зависит от локального polling. Если локальный процесс остановить, бот перестаёт отвечать. Это нужно закрыть до Step 8.

Что уже есть
- Railway backend API live
- Railway Postgres connected
- test data seeded
- Mini App UI published as separate Railway service and opens correctly from Telegram as UI
- новый Telegram-бот уже создан и токены обновлены
- private chat flow и команды уже существуют
- локальный polling работает
- webhook route в проекте уже был/есть, но нужно привести staging к реально рабочему состоянию для нового бота

Цель этого среза
Сделать так, чтобы новый Telegram-бот:
1. отвечал через Railway webhook без локального polling
2. продолжал открывать Mini App через уже рабочий Railway Mini App URL
3. не требовал локального процесса `python -m app.bot.runner`
4. не ломал текущие команды, CTA, Mini App flow и текущую логику бронирования

Жёсткие границы scope
Не менять:
- booking/payment business logic
- Mini App screens/UX
- API contract кроме минимально необходимого для webhook health/registration if needed
- migrations
- data model
- waitlist/handoff/admin scope
- Step 8

Нужно сделать
1. Проверить текущую webhook-ready инфраструктуру в коде:
   - где формируется webhook URL
   - где используется TELEGRAM_WEBHOOK_SECRET
   - как регистрируется webhook
   - есть ли startup/hook helper или отдельная команда для setWebhook
2. Привести код к одному понятному staging flow:
   - Railway backend service принимает Telegram webhook updates
   - новый бот может быть зарегистрирован на этот webhook URL
   - локальный polling остаётся только как dev fallback, но staging/prod не зависит от него
3. Если нужно — добавить безопасную отдельную operational команду/скрипт для:
   - set webhook
   - delete webhook
   - show webhook info
   для нового бота, без скрытой магии
4. Использовать environment-driven configuration:
   - TELEGRAM_BOT_TOKEN
   - TELEGRAM_BOT_USERNAME
   - TELEGRAM_WEBHOOK_SECRET
   - TELEGRAM_MINI_APP_URL
   - backend public base URL / host if needed
5. Убедиться, что private chat `/start` и CTA `Deschide Mini App` продолжают работать после webhook switch
6. Явно отделить:
   - dev local polling mode
   - Railway webhook mode
7. Сделать это минимально-инвазивно и безопасно

Ожидаемый результат
После настройки:
- локальный polling можно выключить
- новый бот продолжает отвечать в Telegram
- `/start` работает через Railway
- Mini App открывается через уже рабочий Railway Mini App UI
- staging становится целостным перед Step 8

Предпочтительная реализация
- сохранить `python -m app.bot.runner` как dev-mode polling entry
- добавить/уточнить явный webhook operational path для Railway
- не делать автоматическую опасную регистрацию webhook в неожиданных местах без документации
- лучше иметь явную команду/скрипт + понятную документацию

Вероятные файлы в scope
- app/bot/runner.py
- app/bot/... связанные webhook/bootstrap файлы
- app/api/routes/... telegram webhook route
- app/core/config.py
- docs/...
- optional scripts/... for webhook ops

Нужно также обновить документацию
Создать или обновить:
- docs/TELEGRAM_WEBHOOK_STAGING.md

В документации обязательно указать:
1. какой сервис принимает webhook
2. какой exact webhook URL должен быть у нового бота
3. как используется TELEGRAM_WEBHOOK_SECRET
4. какие env vars обязательны
5. как включать dev polling локально
6. как зарегистрировать webhook вручную
7. как проверить webhook info
8. как откатиться обратно безопасно
9. smoke test checklist:
   - `/start`
   - команды
   - CTA open mini app
   - Mini App opens
   - local polling stopped but bot still answers

Очень важно
- не начинать Step 8
- не менять продуктовый flow
- не ломать текущий локальный dev сценарий
- не завязывать решение на ручные хаки без документации
- все operational steps должны быть воспроизводимыми

Перед кодом кратко сообщи:
1. почему текущий state ещё не готов для Step 8
2. какой webhook slice ты реализуешь
3. почему он безопасен

После кодирования отчитайся строго в формате:
1. изменённые файлы
2. что именно поменялось в webhook flow
3. локальные команды для dev polling
4. команды/шаги для Railway webhook registration
5. необходимые env vars
6. smoke-test steps
7. что осталось вне scope