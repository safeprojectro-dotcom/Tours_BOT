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
- Phase 7 / Step 11 completed:
  - read-side work-state visibility for assigned `group_followup_start`
- Phase 7 / Step 12 completed:
  - narrow operator take-in-work mutation for assigned `group_followup_start`
- Combined Phase 7 / Step 13–14 completed:
  - narrow resolve/close mutation for `group_followup_start`
  - tiny resolved-state read-side refinement
- public booking/payment/waitlist/Mini App flows must remain untouched
- future track `per_seat / full_bus` remains separate and explicitly out of scope

Текущая задача:
Phase 7 / Step 15

Нужен только один узкий safe slice:
POST-RESOLUTION OPERATOR QUEUE VISIBILITY / FILTER REFINEMENT FOR `group_followup_start`

Важно:
это НЕ новый workflow engine.
Это НЕ новый mutation.
Это only a narrow read-side/operator queue refinement after the resolve flow already exists.

Что именно сделать:
1. Improve existing admin handoff read/list surface so resolved `group_followup_start` handoffs are easier to distinguish in queue/list usage.
2. Prefer extending existing list/detail models and list filtering behavior minimally.
3. No write-path changes.

Preferred safe direction:
- add one narrow derived/read-only queue signal for resolved `group_followup_start`, such as:
  - `is_resolved_group_followup`
  - `queue_bucket`
  - `followup_queue_state`
- optionally add a very narrow list filter if the current admin handoff list already supports comparable filtering patterns and the addition stays small
- if a filter would widen scope too much, keep this step read-only fields only

Expected narrow behavior:
- admin handoff list/detail clearly communicates when a `group_followup_start` handoff is:
  - open/unassigned
  - assigned/in work
  - resolved/closed
- resolved `group_followup_start` should be easier to identify without changing write semantics
- ordinary handoffs must not receive false group-followup-specific visibility fields

Implementation rules:
1. Keep repositories persistence-oriented only.
2. Keep derived logic in read/service layer.
3. Prefer extending existing admin handoff schemas/models rather than creating new routes.
4. No schema migration unless absolutely unavoidable; prefer not to require one.
5. Do not change existing assignment / in-work / resolve logic.

Validation / safety rules:
- no operator assignment changes
- no claim/reassign changes
- no workflow state expansion
- no booking/payment side effects
- no Mini App/public flow changes
- no new persistence semantics

Allowed scope:
- narrow read-side additions
- minimal schema updates for admin handoff read models
- focused tests only
- optional tiny existing-route filter refinement only if clearly small and justified

Запрещено в этом шаге:
- operator assignment changes
- claim / takeover engine
- new workflow statuses
- booking/payment mutations
- public API expansion beyond minimal existing admin read surface
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
2. перечисли read-side/schema changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть, что resolved `group_followup_start` handoff в list/detail читается с новым queue/readiness signal
- покрыть, что in-review/open variants читаются без ложного resolved-signal
- покрыть, что ordinary/non-group-followup handoff не получает ложный signal
- покрыть, что mutation semantics не изменились
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие read-side/schema changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed