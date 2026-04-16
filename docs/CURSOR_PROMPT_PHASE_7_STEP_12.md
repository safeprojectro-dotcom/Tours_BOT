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
- public booking/payment/waitlist/Mini App flows must remain untouched
- future track `per_seat / full_bus` exists conceptually but is explicitly out of scope for this step

Текущая задача:
Phase 7 / Step 12

Нужен только один узкий safe slice:
NARROW OPERATOR ACKNOWLEDGE / TAKE-IN-WORK MUTATION FOR ASSIGNED `group_followup_start` HANDOFFS

Важно:
это НЕ полный workflow engine.
Это НЕ broad takeover/claim redesign.
Это only one narrow post-assignment operator action for the already assigned `group_followup_start` handoffs.

Что именно сделать:
1. Add one narrow mutation path so an already assigned `group_followup_start` handoff can be explicitly acknowledged / taken into work.
2. Reuse existing handoff mutation patterns if present.
3. Keep scope extremely narrow:
   - only for `group_followup_start`
   - only after assignment exists
   - only one post-assignment action
   - no notifications
   - no broader workflow redesign

Expected narrow behavior:
- choose one safe endpoint pattern, preferably on existing admin handoff mutation surface, for example:
  - `POST /admin/handoffs/{handoff_id}/mark-in-work`
  or similarly narrow wording
- allowed only when:
  - handoff exists
  - handoff reason is `group_followup_start`
  - assigned_operator_id is present
  - current status is suitable for this narrow transition
- idempotent if already in the target “in work” state
- safe client error if:
  - handoff not found
  - handoff reason is not `group_followup_start`
  - no operator assigned yet
  - current state does not allow this narrow action

Implementation rules:
1. Keep repositories persistence-oriented only.
2. Keep business rules in service layer.
3. Prefer reusing existing handoff/admin read surface for the response.
4. No schema migration unless absolutely unavoidable; prefer not to require one.
5. No workflow broadening beyond this narrow action.

Validation / safety rules:
- no booking/payment side effects
- no Mini App/public flow changes
- no notifications
- no broad claim queue or takeover redesign
- no assignment logic changes beyond using the already assigned state

Allowed scope:
- one narrow operator work-start mutation
- minimal service/route additions needed for this action
- focused tests only

Запрещено в этом шаге:
- broad claim engine
- reassignment redesign
- notifications
- booking/payment mutations
- public API expansion beyond this narrow admin mutation
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
2. перечисли service/repository/route changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть successful acknowledge / in-work transition for assigned `group_followup_start`
- покрыть not-found handoff
- покрыть that non-`group_followup_start` handoff cannot use this path
- покрыть that unassigned `group_followup_start` cannot use this path
- покрыть idempotent behavior if already in target state
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие service/repository/route changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed