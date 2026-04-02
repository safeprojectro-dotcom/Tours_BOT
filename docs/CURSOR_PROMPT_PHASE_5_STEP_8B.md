Перед кодом (кратко)
Фаза: Phase 5 / Step 8B stabilization
Причина: после Step 8A staging стал заметно стабильнее, но ручной smoke-test выявил ещё 4 product-facing дефекта:
1. mobile scroll исправлен только на catalog screen; detail/prepare/booking-related screens ещё не унифицированы
2. Mini App UI-shell не переводится полностью на выбранный язык
3. TEST_BELGRADE_001 часто остаётся sold out / unavailable for reservation preparation из-за накопленных staging orders/holds/payments
4. В БД по test tour есть несколько orders/payments, но My bookings показывает только одну запись — нужно явно понять, это expected filtering или defect

Что уже работает
- Railway API live
- Railway webhook для Telegram bot live
- Mini App UI live на отдельном Railway service
- Bot commands работают
- Main catalog scroll на mobile уже исправлен
- View details теперь достижим на телефоне
- TEST_BELGRADE_001 seeded
- Manual smoke уже проходил catalog → detail → bookings → payment screens

Цель этого среза
Сделать staging Mini App и booking visibility предсказуемыми и пригодными для расширенного smoke-test:
1. все ключевые Mini App pages должны корректно скроллиться на телефоне
2. UI-shell Mini App должен переводиться на выбранный язык, даже если content tour fallback-ится
3. нужно стабилизировать TEST_BELGRADE_001 для повторяемого prepare test
4. нужно проверить и явно зафиксировать правила, по которым My bookings показывает записи

Жёсткие границы scope
Не менять:
- booking/payment core business rules
- reconciliation/payment lifecycle
- DB schema / migrations
- webhook flow
- Railway service split
- Step 9+ scope
- provider/admin/handoff/waitlist logic

Разрешённый scope
- Mini App layout unification / shared screen wrapper / scroll helper
- Mini App UI translation keys for shell text, buttons, headers, status labels, navigation labels
- staging reset / audit script(s) только для TEST_BELGRADE_001
- audit/debug output or docs for My bookings filtering
- smoke-test docs

Что нужно сделать
1. Проанализировать все ключевые Mini App screens и унифицировать mobile scroll:
   как минимум проверить и починить:
   - catalog
   - tour detail
   - prepare
   - my bookings
   - booking detail
   - payment
   - help
   - settings
   Желательно не локальными правками по месту, а общим reusable layout/wrapper pattern, если это безопасно.
2. Исправить Mini App UI localization shell:
   На выбранном языке должны отображаться, где возможно:
   - screen titles
   - navigation labels
   - action buttons
   - common helper texts
   - status labels like sold out / open for sale / seats available / my bookings / prepare reservation / help / settings / back to ...
   При этом:
   - сам tour content (title/description/program text/boarding notes) может fallback-иться, если перевода нет
   - это нормально, но должно быть явно и аккуратно показано
3. Проанализировать TEST_BELGRADE_001 availability:
   - почему после reset/seed тур снова уходит в sold out
   - проверить, корректно ли reset script реально очищает связанные active holds/orders/payments именно для этого тура
   - если надо, доработать reset script, не меняя бизнес-правила
   - после reset test tour должен снова быть пригоден для ручного prepare smoke-test
4. Проанализировать My bookings:
   - по каким полям/условиям Mini App фильтрует бронирования
   - почему в БД много orders/payments, а текущему пользователю показывается только одна запись
   - если это expected behavior, задокументировать
   - если это defect — исправить минимально и безопасно
5. Обновить документацию:
   - docs/PHASE_5_STEP_8_SMOKE_CHECK.md
   - при необходимости новый docs/PHASE_5_STEP_8B_NOTES.md
   В документации зафиксировать:
   - какие страницы обязаны скроллиться
   - что переводится, а что fallback-ится
   - как reset-ить TEST_BELGRADE_001
   - как интерпретировать My bookings vs orders in DB

Ожидаемый результат
После фикса:
- все основные Mini App screens usable на телефоне
- language selection влияет на UI-shell Mini App
- TEST_BELGRADE_001 можно стабильно вернуть в состояние available for reservation preparation
- поведение My bookings понятно и документировано
- staging готов к более длинному regression smoke-test

Вероятные файлы в scope
- mini_app/app.py
- mini_app/... screen files / helpers / shared layout wrappers
- app/services/... or app/repositories/... where bookings listing/filtering is assembled
- scripts/reset_test_belgrade_tour_state.py
- scripts/seed_test_belgrade_tour.py
- docs/PHASE_5_STEP_8_SMOKE_CHECK.md
- optional docs/PHASE_5_STEP_8B_NOTES.md

Очень важно
- не делать большой refactor ради красоты
- не менять product rules
- fixes только staging-safe и объяснимые
- reset должен быть ограничен TEST_BELGRADE_001
- если My bookings current behavior expected, не “чинить” его насильно — лучше объяснить и задокументировать

Перед кодом сообщи кратко:
1. какие 4 дефекта подтверждены
2. какой минимальный safe slice будет сделан
3. что будет исправлено кодом, а что только задокументировано

После кодирования отчитайся строго в формате:
1. изменённые файлы
2. что исправлено в shared Mini App scroll/layout
3. что исправлено в Mini App localization shell
4. что выяснено и/или исправлено по TEST_BELGRADE_001 availability
5. что выяснено и/или исправлено по My bookings filtering
6. обновлённые smoke-test steps
7. что осталось вне scope
