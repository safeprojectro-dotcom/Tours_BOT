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
  - allowed triggers, CTA routing, anti-spam, and handoff categories are documented
- no production/runtime Telegram group behavior has been changed yet
- public booking/payment/waitlist/Mini App flows must remain untouched

Текущая задача:
Phase 7 / Step 2

Нужен только один узкий safe slice:
GROUP TRIGGER EVALUATION + HANDOFF TRIGGER HELPER FOUNDATION

Важно:
это НЕ полный Telegram group runtime yet.
Это только внутренние helper/service functions plus focused tests.

Что именно сделать:
1. Добавить узкий внутренний модуль(и) для:
   - group trigger evaluation
   - handoff trigger evaluation / categorization
2. Не подключать это ещё к реальному group message processing runtime, если это расширяет scope слишком сильно.
3. Сделать helpers/service-layer first, чтобы позже безопасно подключить их в bot runtime.

Что должны уметь helpers:
1. Group trigger evaluation:
   - определить, должен ли бот вообще отвечать в группе
   - поддержать только narrow rules:
     - mention
     - approved command
     - approved trigger phrase
   - при этом не превращать это в полный NLP/router engine

2. Handoff trigger evaluation:
   - по тексту/контексту определить, попадает ли кейс в documented handoff categories:
     - discount request
     - group booking
     - custom pickup
     - complaint
     - unclear payment issue
     - explicit human request
     - low-confidence-safe fallback category only if already justified
   - вернуть machine-friendly structured result, not just prose

3. Keep outputs narrow and explicit, for example:
   - should_respond_in_group: bool
   - group_trigger_reason: ...
   - handoff_required: bool
   - handoff_category: ...
Do not overdesign.

4. Keep implementation grounded in:
   - docs/GROUP_ASSISTANT_RULES.md
   - docs/AI_ASSISTANT_SPEC.md
   - docs/AI_DIALOG_FLOWS.md
   - docs/TELEGRAM_SETUP.md

5. Keep runtime boundaries clean:
   - repositories untouched unless absolutely necessary
   - business/rules logic in helper/service layer
   - no real bot handler rewiring unless a tiny safe hook is absolutely needed
   - no public booking/payment/Mini App logic changes

Очень важно:
- do not build full group responder runtime in this step
- do not add long-form AI chat logic
- do not add real operator workflow engine
- do not create actual handoff persistence automatically
- do not touch payment/booking/public flows
- do not widen into moderation or spam-detection subsystem

Разрешённый scope:
- narrow helper/service logic
- small schema/typing additions if truly needed
- focused unit tests
- optional tiny non-invasive integration hook only if absolutely necessary and safe

Запрещено в этом шаге:
- full Telegram group runtime behavior
- broad bot refactor
- operator workflow engine
- booking/payment mutations
- public Mini App changes
- admin/payment workflow expansion
- broad NLP intent router redesign

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли helper/service changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть group trigger evaluation:
  - mention
  - approved command
  - approved trigger phrase
  - non-trigger case
- покрыть handoff trigger categorization минимум для:
  - discount
  - group booking
  - custom pickup
  - complaint
  - unclear payment issue
  - explicit human request
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие helper/service changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed