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
- Phase 7 / Step 6 completed:
  - narrow private `/start` branching for `grp_private` / `grp_followup`
- public booking/payment/waitlist/Mini App flows must remain untouched
- important: Step 6 changed private entry behavior, not group runtime behavior; do not reinterpret unchanged group behavior as a reason to widen scope

Текущая задача:
Phase 7 / Step 7

Нужен только один узкий safe slice:
NARROW RUNTIME HANDOFF PERSISTENCE FOUNDATION FROM `grp_followup`

Важно:
это НЕ полный operator workflow.
Это НЕ assignment engine.
Это only a narrow persistence step from the already established group → private followup chain.

Что именно сделать:
1. Add one narrow persisted handoff intent when a user enters private via:
   - `/start grp_followup`
2. Keep `grp_private` behavior unchanged.
3. Keep scope very narrow:
   - no operator assignment
   - no workflow engine expansion
   - no booking/payment side effects
   - no public API changes

Expected narrow behavior:
- when `/start grp_followup` is handled in private:
  - create one handoff row with a narrow dedicated reason, e.g. `group_followup_start`
- if the same user repeats `/start grp_followup` while a matching open handoff already exists:
  - do NOT create duplicate open rows
- if the previous matching handoff is already closed:
  - a new row may be created
- `/start grp_private` must not create handoff persistence

Implementation rules:
1. Reuse the existing handoff persistence/service patterns already present in the project.
2. Keep business logic in service layer.
3. Keep repositories persistence-oriented only.
4. Do not widen handoff schema/workflow unless truly required.
5. Prefer the narrowest additive change.

Validation / safety rules:
- dedupe repeated follow-up starts by user + reason among open handoffs
- no operator assignment
- no workflow status expansion
- no notification side effects unless already trivial and explicitly safe
- no booking/payment state changes
- no Mini App/public flow changes

Allowed scope:
- narrow handoff reason addition if needed
- one service-layer persistence entry point
- one repository helper for dedupe lookup if needed
- narrow private runtime hook from `grp_followup`
- focused tests only

Запрещено в этом шаге:
- full operator workflow engine
- assignment / claim
- long conversational redesign
- booking/payment mutations
- public API changes
- Mini App changes
- broad refactor

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли service/repository/runtime changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть создание handoff для `/start grp_followup`
- покрыть dedupe: повторный `/start grp_followup` не создаёт второй open row
- покрыть, что после закрытия matching handoff новая запись может быть создана
- покрыть, что `/start grp_private` не создаёт handoff
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие service/repository/runtime changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed