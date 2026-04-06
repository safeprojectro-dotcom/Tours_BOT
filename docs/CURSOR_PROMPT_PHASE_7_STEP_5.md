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
- Phase 7 / Step 4 completed:
  - narrow runtime use of handoff trigger evaluation / escalation recommendation only
- public booking/payment/waitlist/Mini App flows must remain untouched

Текущая задача:
Phase 7 / Step 5

Нужен только один узкий safe slice:
PRIVATE CTA / DEEP-LINK ROUTING FOUNDATION FOR GROUP REPLIES

Важно:
это НЕ полный sales flow.
Это НЕ group booking flow.
Это only a narrow helper/runtime slice so group replies can point users into the correct private-chat entry more consistently.

Что именно сделать:
1. Add a narrow helper/service for building safe private CTA targets from group context.
2. Wire it into the current minimal group reply behavior only where appropriate.
3. Keep it extremely narrow:
   - no booking creation
   - no payment initiation
   - no handoff persistence
   - no Mini App runtime changes
   - no campaign engine

Предпочтительный safe вариант:
- generate one consistent private-chat CTA/deep-link target
- optionally support one minimal mode distinction:
  - generic private support/sales entry
  - human-follow-up flavored private entry for handoff-like categories
But do not overdesign.

Что должно уметь решение:
1. Build a safe private routing target for group replies:
   - bot private deep link or equivalent narrow routing token
   - grounded in current Telegram/bot setup assumptions
2. Keep output machine-friendly and testable, for example:
   - target_url / deep_link
   - entry_mode
   - cta_label or cta_text if truly needed
3. Reuse current trigger/handoff category results where useful, but do not widen into a full router.

Runtime behavior in this step:
- current short safe group reply may now include a clearer private CTA
- reply must remain short
- reply must remain safe
- reply must not promise anything not yet implemented
- if runtime integration becomes too wide, keep the helper/service only and stop there

Что нельзя:
- no actual handoff record creation
- no operator assignment
- no booking/payment logic in group
- no Mini App logic rewrite
- no broad campaign/deep-link subsystem
- no public sensitive data collection in group

Runtime boundaries:
- keep helper logic in service/helper layer
- keep Telegram runtime hookup minimal
- do not refactor whole bot runtime
- do not change public booking/payment flows

Разрешённый scope:
- narrow private CTA/deep-link helper
- minimal runtime reply integration if safe
- focused tests only

Запрещено в этом шаге:
- full Telegram group assistant behavior
- handoff persistence
- operator workflow engine
- booking/payment mutations
- public Mini App changes
- broad deep-link/campaign system
- broad NLP/router redesign

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли helper/runtime changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть generation of private CTA/deep-link target
- покрыть one generic group trigger case
- покрыть one handoff-like category case if supported
- покрыть that non-trigger still stays silent / unchanged
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие helper/runtime changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed