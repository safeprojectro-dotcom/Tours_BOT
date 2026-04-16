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
- Phase 7 / Step 15 completed:
  - post-resolution operator queue visibility / filter refinement for `group_followup_start`
- public booking/payment/waitlist/Mini App flows must remain untouched
- future track `per_seat / full_bus` remains separate and explicitly out of scope

Текущая задача:
Phase 7 / Step 16

Нужен только один узкий safe slice:
NARROW PRIVATE USER-FACING FOLLOWUP CONFIRMATION FOR RESOLVED `group_followup_start`

Важно:
это НЕ полноценный operator reply system.
Это НЕ two-way human chat.
Это only a minimal user-facing confirmation surface so the private flow can reflect that a `group_followup_start` request was resolved.

Что именно сделать:
1. Add a narrow read/query path that allows the private bot flow to detect whether the latest relevant `group_followup_start` handoff for the user has been resolved.
2. If that resolved state is detected in a safe, narrow place in private flow, show one short confirmation-style private message.
3. Keep scope extremely narrow:
   - no operator chat
   - no notification delivery subsystem
   - no free-form replies
   - no booking/payment changes

Preferred safe direction:
- reuse existing private `/start grp_followup` or a similarly narrow private entry surface
- if the user comes again through the `grp_followup` path and there is already a recent resolved `group_followup_start`, show a short closure-style message instead of only the generic followup intro
- do not invent operator names, promised callbacks, or custom data unless already present and reliable

Expected narrow behavior:
- private `grp_followup` entry can distinguish:
  - no relevant handoff yet / open chain
  - resolved recent `group_followup_start`
- if resolved recent handoff is found:
  - show one short safe resolution confirmation message
- if not:
  - keep existing Step 6/7 behavior intact
- no write semantics should change in this step unless a tiny read helper requires an existing repository query

Implementation rules:
1. Keep repositories persistence-oriented only.
2. Keep business logic in service layer or private handler support layer.
3. Prefer one tiny query/helper over broad conversation changes.
4. No schema migration unless absolutely unavoidable; prefer not to require one.
5. Do not change existing assignment / in-work / resolve logic.

Validation / safety rules:
- no operator assignment changes
- no claim/reassign changes
- no workflow state expansion
- no booking/payment side effects
- no Mini App/public flow changes
- no new persistence semantics
- no notification system

Allowed scope:
- narrow read/query helper
- minimal private-flow adaptation for one short resolved confirmation message
- focused tests only

Запрещено в этом шаге:
- operator reply/chat system
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
- покрыть, что private `grp_followup` shows resolved confirmation when latest relevant handoff is resolved
- покрыть, что open/in_review variants do not falsely show resolved confirmation
- покрыть, что non-group-followup handoff does not trigger the resolved confirmation
- покрыть, что existing private `grp_private` flow remains unchanged
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие service/repository/private-flow changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed