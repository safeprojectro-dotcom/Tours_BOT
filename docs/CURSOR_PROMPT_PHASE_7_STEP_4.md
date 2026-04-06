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
- Phase 7 / Step 1 completed:
  - documentation-first group foundation
- Phase 7 / Step 2 completed:
  - helper/service foundation for group trigger evaluation and handoff trigger categorization
- Phase 7 / Step 3 completed:
  - minimal group runtime gating with one short safe ack
- public booking/payment/waitlist/Mini App flows must remain untouched

Текущая задача:
Phase 7 / Step 4

Нужен только один узкий safe slice:
NARROW RUNTIME USE OF HANDOFF TRIGGER EVALUATION / ESCALATION RECOMMENDATION ONLY

Важно:
это НЕ full operator workflow.
Это НЕ handoff persistence.
Это only a minimal runtime use of handoff trigger evaluation to shape the bot’s short safe reply behavior.

Что именно сделать:
1. Reuse Step 2 handoff trigger helpers in the current narrow group runtime.
2. If a group message triggers a documented handoff category, the bot may slightly adapt its short reply:
   - acknowledge briefly
   - suggest private chat / human follow-up path
   - but do not create real handoff records yet
3. Keep replies short and safe.

Examples of runtime behavior allowed in this step:
- discount request -> short reply that custom conditions require private/human follow-up
- group booking -> short reply that larger requests should continue in private
- complaint -> short reply that a human should review it
- explicit human request -> short reply that support/private path is available
- unclear payment issue -> short reply that payment-sensitive issues should continue privately

Что нельзя:
- no real handoff persistence
- no operator assignment
- no workflow engine
- no long replies
- no booking/payment resolution in group
- no public sensitive data collection
- no broad sales flow in group

Runtime boundaries:
- keep using existing minimal group gating runtime
- do not refactor whole Telegram runtime
- keep helper logic in service/helper layer
- wiring should remain as narrow as possible

Reply behavior:
- short
- safe
- category-aware when needed
- no invented facts
- no real promises that a human was already assigned unless that is actually true

Разрешённый scope:
- narrow runtime use of handoff trigger categorization
- minimal reply policy refinement
- focused tests only

Запрещено в этом шаге:
- full Telegram group assistant behavior
- handoff persistence
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
2. перечисли runtime/reply-policy changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть минимум:
  - discount trigger reply shape
  - group booking trigger reply shape
  - complaint trigger reply shape
  - explicit human request reply shape
  - non-trigger still stays silent
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие runtime/reply-policy changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed