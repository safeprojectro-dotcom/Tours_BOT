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
- Phase 7 / Steps 1–17 completed
- current chain already includes:
  - group trigger handling
  - group→private deep-link routing
  - `grp_followup` private branching
  - narrow handoff persistence
  - operator visibility / assignment / in-work / resolve
  - queue-state visibility
  - private resolved confirmation
  - compact private followup readiness/history signal
- public booking/payment/waitlist/Mini App flows must remain untouched
- future track `per_seat / full_bus` remains explicitly out of scope for this block

Текущая задача:
FINAL PHASE 7 FOLLOWUP UX / READ-SIDE CONSOLIDATION BLOCK

Нужен один укрупнённый, но всё ещё safe block:
1. private CTA / wording refinement for active/open `grp_followup`
2. private CTA / wording refinement for assigned/in_work `grp_followup`
3. consistency cleanup between private followup messaging and admin queue/read-side terminology
4. focused final tests for the full `grp_followup` chain
5. no new workflow capabilities

Важно:
это НЕ новый operator chat.
Это НЕ notification system.
Это НЕ broad private assistant redesign.
Это НЕ new business track.
Это only a final polish/consolidation block for the already built Phase 7 followup chain.

Что именно сделать:
1. Refine private `grp_followup` user-facing messaging so active/open, assigned/in_work, and resolved states feel coherent and non-contradictory.
2. Keep all messages:
   - short
   - safe
   - non-committal
   - without operator names, timing promises, or internal jargon
3. Reuse existing handoff/read-side state mapping where possible.
4. Add focused final tests covering the major end states of the chain.
5. Do not add new persistence, mutation types, or workflow states.

Preferred safe direction:
- keep one compact helper or a tiny set of helper functions mapping internal handoff state to user-facing followup message keys
- only touch the `grp_followup` private path
- leave `grp_private` unchanged
- keep admin read-side semantically aligned, but do not create a new admin feature surface

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
- no `per_seat / full_bus` implementation work

Allowed scope:
- private followup wording / CTA refinement
- tiny helper consolidation
- tiny read-side consistency cleanup if needed
- focused final tests only

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
3. что входит в этот final consolidation block
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли service/private-flow/read-side changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть private `grp_followup` messaging for:
  - active/open
  - assigned/in_work
  - resolved
- покрыть that non-group-followup handoff does not falsely trigger these messages
- покрыть `grp_private` remains unchanged
- покрыть that existing mutation semantics are untouched
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие service/private-flow/read-side changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed