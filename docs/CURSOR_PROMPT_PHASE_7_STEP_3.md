Продолжаем Tours_BOT от последнего approved checkpoint.

Используй как source of truth:
1. docs/IMPLEMENTATION_PLAN.md
2. docs/CHAT_HANDOFF.md
3. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
4. docs/PHASE_6_REVIEW.md
5. docs/TESTING_STRATEGY.md
6. docs/AI_ASSISTANT_SPEC.md
7. docs/AI_DIALOG_FLOWS.md
8. docs/TECH_SPEC_TOURS_BOT.md
9. docs/TELEGRAM_SETUP.md
10. docs/GROUP_ASSISTANT_RULES.md

Контекст:
- Phase 6 review accepted and transition completed
- Phase 7 / Step 1 completed:
  - documentation-first foundation for group behavior and handoff rules
- Phase 7 / Step 2 completed:
  - helper/service foundation for group trigger evaluation
  - helper/service foundation for handoff trigger categorization
- no production Telegram group runtime behavior has been changed yet
- public booking/payment/waitlist/Mini App flows must remain untouched

Текущая задача:
Phase 7 / Step 3

Нужен только один узкий safe slice:
FIRST NARROW GROUP RUNTIME HOOKUP FOR TRIGGER GATING ONLY

Важно:
это НЕ полный group assistant yet.
Это только первый минимальный runtime hookup, чтобы бот в группе начал:
- распознавать, когда он вообще должен реагировать,
- и безопасно НЕ реагировать в остальных случаях.

Что именно сделать:
1. Подключить helper-layer из Step 2 к самому узкому runtime месту в group message handling.
2. Scope должен быть только такой:
   - если group trigger НЕ сработал → бот молчит
   - если group trigger сработал → пока допускается только very narrow placeholder / safe acknowledgment behavior
3. Не подключать ещё full CTA logic, full booking assistance, handoff persistence, long-form group replies, operator workflow.

Предпочтительный безопасный вариант:
- wired group handler only decides:
  - ignore
  - or produce one short safe response path
- при этом reply content должен быть очень ограниченным и не пытаться решать booking/payment прямо в группе

Что разрешено:
- mention
- approved command
- approved trigger phrase
- very short response on triggered cases

Что не разрешено в этом шаге:
- широкие ответы в группе
- полноценный подбор тура в группе
- реальные handoff записи
- сбор личных данных
- обсуждение payment-sensitive details в группе
- длинная conversational logic
- массовая активация бота на всё подряд

4. Runtime boundaries:
- использовать уже реализованные helper functions из Step 2
- не переписывать весь Telegram runtime
- делать узкий hook только там, где group messages уже проходят
- если в проекте пока нет безопасной точки подключения group runtime без лишнего расширения, выбрать самый минимальный integration point и явно это задокументировать

5. Reply behavior:
- если нужен reply, он должен быть:
  - коротким
  - безопасным
  - без invented facts
  - с CTA в private / Mini App только в самом базовом виде
- reply policy не должна превращаться в полноценный sales flow в группе в этом шаге

6. Testing:
- focused tests only
- при необходимости добавить unit tests around runtime gating behavior
- если runtime layer сложно unit-testить напрямую, покрыть helper-to-runtime boundary минимально и безопасно

Очень важно:
- do not build full group responder runtime
- do not add long-form AI chat logic
- do not add actual handoff persistence
- do not add operator workflow engine
- do not touch booking/payment/public Mini App flows
- do not widen into moderation or spam-detection subsystem
- do not make the bot answer every group message

Разрешённый scope:
- minimal runtime hookup for trigger gating only
- minimal safe short response behavior
- focused tests only

Запрещено в этом шаге:
- full Telegram group assistant behavior
- broad bot refactor
- operator workflow engine
- booking/payment mutations
- public Mini App changes
- admin/payment workflow expansion
- broad NLP/router redesign

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли runtime hookup changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть, что бот НЕ реагирует на non-trigger group message
- покрыть mention-trigger case
- покрыть approved command case
- покрыть approved trigger phrase case
- покрыть, что reply remains short/safe if implemented
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие runtime hookup changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed