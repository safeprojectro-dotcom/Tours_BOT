Перед кодом (кратко)
Фаза: Phase 5 / Step 9A — configurable hold TTL for staging
Причина:
- reservation/payment lifecycle уже стабилизирован lazy expiry
- для ручного тестирования ждать длинный hold неудобно
- нужен маленький безопасный шаг: вынести TTL временной брони в конфиг/env, чтобы на staging поставить 15 минут, а позже легко вернуть другое значение
- это НЕ redesign booking/payment logic, а только configurability текущего TTL

Цель этого среза
Сделать время жизни temporary reservation настраиваемым через env/config, без изменения остальной бизнес-логики.
На staging хотим использовать 15 минут.

Жёсткие границы scope
Не менять:
- Railway split / webhook / Mini App deployment
- schema / migrations
- payment provider integration
- expiry/release semantics
- UI flow
- статусы order/payment
- reset scripts, если для этого шага это не обязательно

Разрешённый scope
- config/settings
- то место, где рассчитывается reservation_expires_at / hold TTL
- docs по env и staging usage
- возможно .env.example
- возможно docs/PHASE_5_STEP_9_NOTES.md update

Что нужно сделать
1. Найти текущее место, где рассчитывается reservation_expires_at для временной брони.
2. Вынести TTL в конфиг, например:
   - TEMP_RESERVATION_TTL_MINUTES
   или
   - RESERVATION_HOLD_MINUTES
   Выбрать одно понятное имя и использовать его последовательно.
3. Добавить значение по умолчанию, чтобы старое поведение не ломалось, если env не задан.
4. Убедиться, что create temporary reservation использует это значение из settings/config, а не hardcoded число.
5. Обновить:
   - .env.example
   - docs/PHASE_5_STEP_9_NOTES.md
   - при необходимости docs/CHAT_HANDOFF.md короткой строкой
6. Никаких изменений в остальной логике hold/payment не делать.

Важно
- Нужен именно маленький safe config slice.
- Не менять бизнес-правила кроме configurable TTL.
- Не добавлять лишние abstraction layers без необходимости.

Ожидаемый результат
После изменения:
- TTL hold берётся из env/config
- на staging можно поставить 15 минут
- позже можно легко вернуть другое значение одной переменной
- текущий flow бронирования остаётся прежним

Предпочтительно
- если проект уже использует Settings / config class, встроить переменную туда
- использовать integer minutes
- защититься от невалидного значения разумным default

Проверка
Сделать минимальную проверку:
- py_compile для изменённых файлов
- если есть подходящий unit test на расчёт expiry — обновить/добавить небольшой тест
- не запускать полный repo-wide test suite

Перед кодом сообщи кратко:
1. где сейчас захардкожен TTL
2. какое имя env будет использовано
3. какое default значение останется

После кодирования отчитайся строго в формате:
1. изменённые файлы
2. где теперь читается TTL
3. какое имя env используется и какой default
4. что нужно поставить на Railway staging для 15 минут
5. какие проверки выполнены
6. что осталось вне scope