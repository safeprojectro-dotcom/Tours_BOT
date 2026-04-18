Продолжаем Tours_BOT от последнего approved checkpoint.

Используй как source of truth:
1. docs/IMPLEMENTATION_PLAN.md
2. docs/CHAT_HANDOFF.md
3. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
4. docs/PHASE_6_REVIEW.md
5. docs/PHASE_7_REVIEW.md
6. docs/TOUR_SALES_MODE_DESIGN.md
7. docs/TESTING_STRATEGY.md
8. docs/TECH_SPEC_TOURS_BOT.md
9. docs/AI_ASSISTANT_SPEC.md
10. docs/AI_DIALOG_FLOWS.md
11. docs/TELEGRAM_SETUP.md
12. docs/GROUP_ASSISTANT_RULES.md

Контекст:
- Phase 7 followup/operator track closed enough for staging/MVP and is not the active implementation track now
- New active sub-track: Phase 7.1 — tour sales mode
- Approved rollout order from docs/TOUR_SALES_MODE_DESIGN.md:
  1. admin/source-of-truth fields
  2. backend service-layer policy
  3. read-side adaptation for Mini App and private bot
  4. operator-assisted full-bus path
  5. only later, if needed, direct whole-bus booking flow
- After completion of Phase 7.1 planned work, the project should return to the main plan and continue with Phase 8 per the approved roadmap
- This sub-track must remain separate from the closed Phase 7 handoff/operator chain

Текущая задача:
PHASE 7.1 / SALES MODE / STEP 1

Нужен только один узкий safe slice:
ADMIN / SOURCE-OF-TRUTH FIELDS FOR TOUR SALES MODE

Важно:
это НЕ booking logic step.
Это НЕ Mini App/UI step.
Это НЕ payment step.
Это only the first admin/source-of-truth slice for the new track.

Что именно сделать:
1. Add tour-level source-of-truth fields needed to represent the approved sales modes:
   - `per_seat`
   - `full_bus`
2. Make these fields available in existing admin read/write surfaces for tours.
3. Keep the implementation minimal and aligned with the approved design.
4. Do not yet change customer-facing booking behavior.

Preferred safe direction:
- add the smallest clean set of fields needed now, based on docs/TOUR_SALES_MODE_DESIGN.md
- strongly prefer:
  - `sales_mode`
  - and, only if justified already in this first slice, `full_bus_price`
- if `bus_capacity` is not strictly needed in this first source-of-truth slice, do not force it yet
- avoid overbuilding for hypothetical future modes

Expected narrow behavior:
- admin can read a tour’s `sales_mode`
- admin can set/update a tour’s `sales_mode`
- if `full_bus_price` is included in this slice, admin can read/set it too
- existing tours should continue to behave safely with a sensible default such as `per_seat`
- no public behavior should change yet

Implementation rules:
1. Preserve architecture: business rules stay in backend/service layer, not in UI.
2. Keep this step source-of-truth only.
3. Prefer minimal DB/model/schema/admin-route changes needed for this slice.
4. If migration is required, make it minimal and safe.
5. Do not add service-layer booking policy yet, unless a tiny placeholder is strictly necessary.
6. Do not adapt Mini App/private bot in this step.
7. Keep this work explicitly under Phase 7.1 naming/continuity, not as a reopening of Phase 7.

Validation / safety rules:
- no booking/payment logic changes
- no public API behavior changes for customer flows
- no Mini App behavior changes
- no private bot booking behavior changes
- no ad hoc mixing with Phase 7 handoff/operator logic
- no direct whole-bus booking yet

Allowed scope:
- model/schema additions for tours
- migration if needed
- admin read/write schema updates
- admin route/service updates for reading/updating these fields
- focused tests only

Запрещено в этом шаге:
- customer-facing booking mode changes
- Mini App UI changes
- private bot UX changes
- payment changes
- operator-assisted full-bus booking
- direct whole-bus booking flow
- broad refactor

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже решено design-документом
3. почему этот шаг только source-of-truth
4. почему этот шаг относится к Phase 7.1
5. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли model/schema/admin read-write changes
3. перечисли test scope
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть default / existing-tour compatibility
- покрыть admin read exposure of new field(s)
- покрыть admin update/change of `sales_mode`
- если есть `full_bus_price` в этом шаге — покрыть его read/write validation
- покрыть, что unrelated existing admin tour behavior не сломано
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие model/schema/admin changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed
7. Подтверждение, что это Phase 7.1 source-of-truth slice и что после завершения под-трека проект должен вернуться к основному плану и перейти к Phase 8