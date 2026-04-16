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
- public booking/payment/waitlist/Mini App flows must remain untouched
- future track `per_seat / full_bus` remains separate and explicitly out of scope

Текущая задача:
Combined Phase 7 / Step 13–14

Нужен один связанный safe block:
1. NARROW OPERATOR CLOSE / RESOLVE MUTATION FOR `group_followup_start`
2. SMALL READ-SIDE REFINEMENT FOR RESOLVED `group_followup_start`

Важно:
это НЕ полный workflow engine.
Это НЕ broad close/reopen redesign.
Это only one narrow resolution action plus one tiny read-side visibility refinement for the same handoff chain.

Часть A — narrow close/resolve mutation
Что именно сделать:
1. Add one narrow mutation path so an in-work / suitable `group_followup_start` handoff can be explicitly closed/resolved.
2. Reuse existing handoff mutation patterns if present.
3. Keep scope extremely narrow:
   - only for `group_followup_start`
   - only one resolution action
   - no notifications
   - no broader workflow redesign

Expected narrow behavior:
- choose one safe endpoint pattern, preferably on existing admin handoff mutation surface, for example:
  - `POST /admin/handoffs/{handoff_id}/resolve`
  or similarly narrow wording
- allowed only when:
  - handoff exists
  - handoff reason is `group_followup_start`
  - current state is suitable for narrow resolution
- prefer narrowest rule:
  - `in_review -> closed`
  - `closed` idempotent
  - `open` rejected unless you have a very strong reason otherwise (prefer reject)
- safe client error if:
  - handoff not found
  - wrong reason
  - current state invalid

Часть B — small read-side refinement for resolved state
Что именно сделать:
1. Extend the existing admin handoff read-side minimally so resolved `group_followup_start` handoffs read more clearly.
2. Prefer one tiny derived/read-only label rather than many fields.

Expected narrow behavior:
- if useful, add one minimal read-only signal, for example:
  - `group_followup_resolution_label`
  - or extend existing work-state label logic to clearly represent resolved state
- keep it tiny
- no new routes
- no write semantics change

Implementation rules:
1. Keep repositories persistence-oriented only.
2. Keep business rules in service layer.
3. Keep read-side derivation in read/service layer.
4. Prefer reusing existing admin handoff read models and response shapes.
5. No schema migration unless absolutely unavoidable; prefer not to require one.

Validation / safety rules:
- no booking/payment side effects
- no Mini App/public flow changes
- no notifications
- no broad claim/reassign/takeover redesign
- no assignment logic changes
- no `per_seat / full_bus` work in this step

Allowed scope:
- one narrow resolve/close mutation
- one tiny read-side refinement tied to resolved `group_followup_start`
- minimal service/route/schema changes needed for this block
- focused tests only

Запрещено в этом шаге:
- broad workflow engine
- reopen redesign
- reassignment redesign
- notifications
- booking/payment mutations
- public API expansion beyond this narrow admin mutation + tiny read-side refinement
- Mini App changes
- broad refactor
- any `per_seat / full_bus` implementation work

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe block
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли service/repository/route/read-side changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть successful resolve/close for `group_followup_start`
- покрыть 404 for missing handoff
- покрыть wrong-reason rejection
- покрыть invalid-state rejection (prefer `open` rejected)
- покрыть idempotent behavior for already `closed` if you choose that rule
- покрыть новый tiny read-side signal for resolved `group_followup_start`
- покрыть, что ordinary/non-group-followup handoff does not get false resolved signal
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие service/repository/route/read-side changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed