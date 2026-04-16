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
- Phase 7 / Steps 1–16 completed
- current chain includes:
  - group trigger handling
  - group→private deep-link routing
  - `grp_followup` private branching
  - narrow handoff persistence
  - operator visibility / assignment / in-work / resolve
  - private resolved confirmation
- public booking/payment/waitlist/Mini App flows must remain untouched
- future track `per_seat / full_bus` remains explicitly out of scope

Текущая задача:
Phase 7 / Step 17

Нужен только один узкий safe slice:
NARROW PRIVATE FOLLOWUP HISTORY / READINESS SIGNAL FOR REPEAT `grp_followup` ENTRIES

Важно:
это НЕ operator chat.
Это НЕ notification system.
Это НЕ broad private assistant redesign.
Это only a small private read-side refinement for repeated `grp_followup` entries.

Что именно сделать:
1. Extend the private `grp_followup` entry logic narrowly so repeated entries can reflect one compact history/readiness signal.
2. Reuse existing handoff query/read patterns if possible.
3. Keep the output extremely short and safe.

Expected narrow behavior:
- private `grp_followup` can now distinguish more clearly among:
  - no relevant handoff yet
  - active/open chain
  - assigned/in work chain
  - resolved chain
- the reply remains short and controlled
- do not expose internal operator IDs or workflow jargon to the user
- do not promise human follow-up timing or invent details

Preferred safe direction:
- keep one tiny helper/service that maps existing handoff state into a very small user-facing followup state
- adapt only the `grp_followup` private entry response path
- do not change `grp_private`
- do not add persistence or mutation logic

Implementation rules:
1. Keep repositories persistence-oriented only.
2. Keep derived logic in service/helper layer.
3. Keep private-flow wording short and safe.
4. No schema migration unless absolutely unavoidable; prefer not to require one.
5. Do not change assignment / in-work / resolve semantics.

Validation / safety rules:
- no operator assignment changes
- no claim/reassign changes
- no workflow state expansion
- no booking/payment side effects
- no Mini App/public flow changes
- no new persistence semantics
- no operator chat or notification delivery system

Allowed scope:
- narrow read/query helper
- minimal private-flow adaptation for one compact followup/readiness signal
- focused tests only

Запрещено в этом шаге:
- operator chat/reply system
- free-form human messaging
- booking/payment mutations
- public API expansion
- Mini App changes
- broad refactor
- any `per_seat / full_bus` implementation work

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли service/repository/private-flow changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть, что repeat `grp_followup` with active/open handoff shows the intended compact readiness signal
- покрыть assigned/in_work variant if supported
- покрыть resolved variant still works correctly
- покрыть non-group-followup handoff does not falsely trigger this signal
- покрыть `grp_private` remains unchanged
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие service/repository/private-flow changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed