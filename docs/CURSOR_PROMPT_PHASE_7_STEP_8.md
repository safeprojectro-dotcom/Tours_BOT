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
- Phase 7 / Step 7 completed:
  - narrow runtime handoff persistence for `grp_followup`
- public booking/payment/waitlist/Mini App flows must remain untouched
- important: Step 7 changed private followup persistence, not group runtime wording; do not widen group behavior because of that

Текущая задача:
Phase 7 / Step 8

Нужен только один узкий safe slice:
FOCUSED RUNTIME / BOT-FLOW TEST COVERAGE FOR THE `grp_followup` CHAIN

Важно:
это НЕ новый feature slice.
Это НЕ operator workflow expansion.
Это a focused validation slice for the already built chain:
group reply deep link -> private `/start grp_followup` -> handoff persistence.

Что именно сделать:
1. Add focused tests around the runtime chain boundary for `grp_followup`.
2. Validate the existing implementation end-to-end as narrowly as possible within the current test setup.
3. Do not widen runtime behavior, storage semantics, or API surface.

What the tests should prove:
1. A `grp_followup` private entry path reaches the runtime handler correctly.
2. It triggers the expected short safe private followup message behavior.
3. It triggers narrow handoff persistence.
4. Repeated `grp_followup` starts do not create duplicate open handoff rows.
5. `grp_private` still does not create handoff persistence.
6. Existing legacy `/start` payload flows remain unchanged.

Implementation rules:
1. Prefer using the current bot/runtime test patterns already present in the repository.
2. Add only the minimum helper/mocking/glue needed for testability.
3. If a tiny non-invasive refactor is required purely to make the runtime path testable, keep it minimal and explicitly justify it.
4. No new business feature should be introduced in this step.

Validation / safety rules:
- no operator assignment
- no workflow engine expansion
- no booking/payment side effects
- no public API changes
- no Mini App changes
- no new persistence semantics beyond what Step 7 already introduced

Allowed scope:
- focused runtime/bot-flow tests
- minimal test support refactor if strictly necessary
- tiny stabilization cleanup only if required for testability

Запрещено в этом шаге:
- new runtime features
- operator workflow engine
- assignment / claim
- booking/payment mutations
- public API changes
- Mini App changes
- broad refactor
- rewriting existing Step 7 behavior

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли test/runtime-boundary changes
3. перечисли exact test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть runtime/private path для `/start grp_followup`
- покрыть, что handoff persistence действительно вызывается из этого пути
- покрыть dedupe behavior на повторном `grp_followup`
- покрыть, что `/start grp_private` не создаёт handoff
- покрыть, что старые `/start` payload flows не сломались
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие test/runtime-boundary changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed