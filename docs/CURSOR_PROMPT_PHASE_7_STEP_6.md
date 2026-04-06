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
  - helper/service foundation for trigger and handoff categorization
- Phase 7 / Step 3 completed:
  - minimal runtime gating
- Phase 7 / Step 4 completed:
  - narrow category-aware escalation wording
- Phase 7 / Step 5 completed:
  - private CTA / deep-link routing foundation
- public booking/payment/waitlist/Mini App flows must remain untouched
- live validation for latest runtime slices may be temporarily deferred due to external Railway deploy incident; do not reinterpret this as a reason to widen or rewrite scope

Текущая задача:
Phase 7 / Step 6

Нужен только один узкий safe slice:
NARROW PRIVATE `/start` BRANCHING FOR `grp_private` / `grp_followup`

Важно:
это НЕ полный private sales flow redesign.
Это only a minimal branching layer so the deep links introduced in Step 5 land more intentionally.

Что именно сделать:
1. Extend private `/start` handling narrowly for:
   - `grp_private`
   - `grp_followup`
2. Keep existing tour/deep-link behavior intact.
3. Do not widen into booking/payment logic.

Expected narrow behavior:
- `grp_private`:
  - sends one short safe private entry message
  - optionally points user toward catalog / normal private flow
- `grp_followup`:
  - sends one short safe private message acknowledging that human/support-style follow-up may continue here
  - but does not create real handoff persistence yet
- other existing `/start` payloads must keep their current behavior

Что нельзя:
- no real handoff record creation
- no operator assignment
- no booking creation
- no payment initiation
- no public sensitive data collection changes
- no full private assistant redesign

Runtime boundaries:
- keep changes narrowly inside private `/start`
- preserve existing route logic for other payloads
- keep wording short and safe
- no invented promises about a human already being assigned

Разрешённый scope:
- narrow `/start` branching for two payloads only
- focused tests only

Запрещено в этом шаге:
- full private chat flow redesign
- handoff persistence
- operator workflow engine
- booking/payment mutations
- Mini App changes
- broad router refactor

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли runtime branching changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть `/start grp_private`
- покрыть `/start grp_followup`
- покрыть, что старые payload flows не сломались
- покрыть, что no persistence / no operator assignment happened
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие runtime branching changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed