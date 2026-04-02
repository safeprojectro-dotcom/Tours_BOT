Перед кодом (кратко)
Фаза: Phase 5 / Step 8
Шаг: связать private chat и Mini App в цельный staging flow после успешного Railway webhook + Mini App UI deployment.
Почему сейчас можно делать этот шаг: staging больше не зависит от локального polling — Telegram-бот работает через Railway webhook, Mini App UI открыт отдельным Railway service, API и DB на Railway, end-to-end smoke проходит.
Что делаем: аккуратный product-facing slice для входа пользователя из private chat в Mini App и обратно, без изменения booking/payment бизнес-логики.

Что уже есть
- Railway API live
- Railway Postgres live
- migrations applied
- test tour seeded
- Mini App UI live on Railway
- Telegram bot работает через Railway webhook
- `/start`, команды, CTA и Mini App open уже работают
- catalog → detail → preparation → booking/payment screen уже доступны
- My bookings / booking detail / payment status уже существуют

Цель Step 8
Сделать user flow между Telegram private chat и Mini App более цельным, понятным и production-like:
1. private chat уверенно ведёт пользователя в Mini App
2. после ключевых действий тексты и CTA в private chat и Mini App согласованы
3. нет мёртвых / confusing entry points
4. staging выглядит как один связный продуктовый сценарий

Жёсткие границы scope
Не менять:
- booking/payment business rules
- reservation lifecycle
- reconciliation logic
- DB schema / migrations
- waitlist / handoff
- admin/provider scope
- webhook transport
- отдельный Mini App deploy model

Разрешённый scope
- private bot copy/CTA
- command responses
- keyboard layout / reply markup / inline CTA
- deep-link / open-mini-app behavior if already supported by Telegram surface
- small UX text alignment between bot and Mini App
- optional safe routing helpers
- docs/checklist for smoke-test

Что нужно сделать
1. Проверить текущий `/start`, `/tours`, `/bookings`, `/help`, `/language`, `/contact` flow в private bot.
2. Привести private chat entry в более цельный сценарий:
   - понятный welcome
   - primary CTA в Mini App
   - secondary CTA to browse in chat if this is still part of MVP
   - убрать дублирующие/слабые формулировки если есть
3. Проверить, как бот формирует кнопку `Deschide Mini App`:
   - должна открывать актуальный `TELEGRAM_MINI_APP_URL`
   - не должно быть старых fallback URL
4. Согласовать названия и тексты:
   - bot CTA
   - Mini App headers / return labels / support wording
   - не идеально финальная i18n, а staging-consistent wording
5. Если есть безопасный способ — улучшить возврат из Mini App в private chat:
   - тексты help/support/back-to-chat
   - без сложной новой логики
6. Проверить “My bookings” entry points:
   - из private chat
   - из Mini App
   - чтобы пользователь не путался, где смотреть статус
7. Оставить весь flow reversible и без product-risk

Предпочтительный результат
После `/start` пользователь сразу понимает:
- где смотреть туры
- что основной современный интерфейс — Mini App
- где смотреть свои бронирования
- куда идти за help/support

Предпочтительная UX-модель
- private chat = guide / launcher / lightweight fallback
- Mini App = основная UI-поверхность каталога и бронирования

Ожидаемый результат для пользователя
1. Открывает бота
2. Видит чистый стартовый сценарий
3. Нажимает Mini App CTA
4. Работает в Mini App
5. Может вернуться к bookings/help без ощущения, что это разные продукты

Вероятные файлы в scope
- app/bot/... handlers / keyboards / copy
- app/content/... если там лежат тексты
- mini_app/app.py только для мелкой согласованности копирайта / labels, если действительно нужно
- docs/...

Нужно также обновить документацию
Создать или обновить:
- docs/PHASE_5_STEP_8_SMOKE_CHECK.md

В документе кратко зафиксировать:
1. expected user journey
2. bot entry points
3. Mini App entry point
4. bookings/status checkpoints
5. exact smoke-test order
6. что не покрывается этим шагом

Очень важно
- не перепридумывать продукт
- не добавлять новые сущности и бизнес-правила
- не ломать существующие API
- не менять Step 9+ scope
- не делать большой refactor
- сохранить staging-safe характер изменений

Перед кодом сообщи кратко:
1. current phase
2. что именно в user journey сейчас рыхлое
3. какой минимальный связующий UX slice ты реализуешь

После кодирования отчитайся строго в формате:
1. изменённые файлы
2. что изменилось в bot entry / CTA flow
3. что изменилось в Mini App wording/navigation (если менялось)
4. smoke-test steps
5. что осталось вне scope