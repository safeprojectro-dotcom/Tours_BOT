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
  - minimal group runtime gating
- Phase 7 / Step 4 completed:
  - narrow category-aware escalation wording
- Phase 7 / Step 5 completed:
  - private CTA / deep-link routing foundation
- Phase 7 / Step 6 completed:
  - narrow private `/start` branching for `grp_private` / `grp_followup`
- Phase 7 / Step 7 completed:
  - narrow runtime handoff persistence for `grp_followup`
- Phase 7 / Step 8 completed:
  - focused runtime/bot-flow test coverage for the `grp_followup` chain
- Phase 7 / Step 9 completed:
  - narrow operator/admin visibility for `group_followup_start`
- Phase 7 / Step 10 completed:
  - narrow operator assignment for `group_followup_start`
- public booking/payment/waitlist/Mini App flows must remain untouched

Текущая задача:
Phase 7 / Step 11

Нужен только один узкий safe slice:
READ-SIDE OPERATOR WORK-STATE VISIBILITY FOR ASSIGNED `group_followup_start` HANDOFFS

Важно:
это НЕ новый workflow engine.
Это НЕ новая assignment logic.
Это НЕ claim/takeover redesign.
Это only a narrow read-side slice so assigned `group_followup_start` handoffs are more clearly visible as “assigned and awaiting/under follow-up”.

Что именно сделать:
1. Extend existing admin/operator handoff read-side narrowly for assigned `group_followup_start` handoffs.
2. Reuse existing handoff list/detail surfaces if possible.
3. Prefer minimal derived/read-only visibility fields over new routes or new status enums.

Expected narrow behavior:
- existing handoff list/detail should expose a clearer visibility/readiness signal for:
  - handoff reason = `group_followup_start`
  - assigned_operator_id is present
- if useful, add one or more narrow derived/read-only fields such as:
  - `is_assigned_group_followup`
  - `operator_followup_state`
  - `work_state_label`
Only add the minimum set that truly improves visibility.
- no mutation behavior should change

Implementation rules:
1. Keep repositories persistence-oriented only.
2. Keep derived logic in read/service layer.
3. Prefer extending existing admin handoff schemas/models rather than creating new routes.
4. No schema migration unless absolutely unavoidable; prefer not to require one.

Validation / safety rules:
- no operator assignment logic changes
- no claim/reassign flow changes
- no workflow status expansion
- no booking/payment side effects
- no Mini App/public flow changes
- no new persistence semantics

Allowed scope:
- narrow read-side additions
- minimal schema updates for admin handoff read models
- focused tests only

Запрещено в этом шаге:
- operator assignment changes
- claim / takeover engine
- booking/payment mutations
- public API expansion beyond minimal existing admin read surface
- Mini App changes
- broad refactor

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли read-side/schema changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть, что assigned `group_followup_start` handoff в list/detail читается с новым work-state/readiness signal
- покрыть, что unassigned `group_followup_start` не получает ложный assigned-signal
- покрыть, что обычные handoff не получают ложный signal
- покрыть, что никакие mutation semantics не изменились
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие read-side/schema changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed