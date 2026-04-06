Продолжаем Tours_BOT от последнего approved checkpoint.

Используй как source of truth:
1. docs/IMPLEMENTATION_PLAN.md
2. docs/CHAT_HANDOFF.md
3. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
4. docs/PHASE_5_ACCEPTANCE_SUMMARY.md
5. docs/TESTING_STRATEGY.md
6. docs/AI_ASSISTANT_SPEC.md
7. docs/AI_DIALOG_FLOWS.md
8. docs/TECH_SPEC_TOURS_BOT.md

Контекст:
- Phase 5 accepted for MVP/staging
- Phase 6 / Steps 1–15 completed:
  - protected admin foundation
  - tours CRUD-like narrow slices
  - boarding point CRUD-like narrow slices
  - tour and boarding point translations narrow slices
  - archive/unarchive for tours
- Phase 6 / Step 16 completed:
  - read-only admin order/payment correction visibility
- Phase 6 / Step 17 completed:
  - read-only admin action preview on order detail
- Phase 6 / Steps 18–22 completed:
  - handoff queue/detail + narrow handoff mutations
- Phase 6 / Steps 23–26 completed:
  - narrow admin order corrections and pre-trip mutation slices
- Phase 6 / Step 27 completed:
  - narrow read-side lifecycle refinement for `ready_for_departure_paid`
- Phase 6 / Step 28 completed:
  - narrow move-readiness decision-support on admin order detail
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, handoffs, and order corrections now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 29

Нужен только один узкий safe slice:
FIRST NARROW ADMIN ORDER MOVE-TO-ANOTHER-TOUR/DATE MUTATION SLICE

Важно:
это НЕ общий move workflow editor.
Это только один very narrow mutation, allowed only for conservatively eligible cases.

Что именно сделать:
1. Добавить только один protected admin mutation endpoint:
   - POST /admin/orders/{order_id}/move
с минимальным телом, только с теми полями, которые абсолютно нужны для narrow move policy
(например target_tour_id and possibly target_boarding_point_id only if strictly required).

2. Цель шага:
- позволить very narrow admin move for carefully eligible orders
- reuse Step 28 move-readiness logic as guardrails where possible
- not open broad manual order editing

3. Validation / safety rules:
- order must exist
- target tour must exist
- use the narrowest safe eligibility policy
- prefer allowing move only when Step 28 readiness is clean / no blockers
- do not move paid/cancelled/problematic orders unless explicitly justified by the chosen narrow rule
- if target tour/date/boarding point makes move unsafe, return safe client error
- seat mutations must be extremely conservative:
  - restore old seats only when new reservation placement succeeds safely
  - reserve target seats safely
  - do not oversell
- do not mutate payment rows
- do not rewrite reconciliation semantics
- do not silently rewrite unrelated order fields

4. Scope of state change:
- update only the minimum necessary fields:
  - `tour_id`
  - maybe `boarding_point_id` if required by chosen rule
  - maybe reservation expiry / derived amount only if absolutely necessary and explicitly justified
- prefer not changing payment state
- prefer not changing booking state unless absolutely necessary
- document the chosen narrow policy clearly

5. Response shape:
- return updated `AdminOrderDetailRead`
- preserve lifecycle fields
- preserve correction visibility fields
- preserve action preview fields
- preserve move-readiness fields if they still apply
- keep route layer thin
- keep transition logic in service layer
- keep repositories persistence-oriented only

Очень важно:
- do not add broad move workflow
- do not add payment mutation
- do not add refund workflow
- do not add move history engine unless trivial and already supported
- do not change webhook behavior
- do not touch public booking/payment flows

Разрешённый scope:
- one narrow admin move mutation only
- minimal schemas/services/repositories needed
- focused tests only

Запрещено в этом шаге:
- payment mutation
- refund workflow
- broad order workflow editor
- publication workflow
- frontend/admin SPA expansion
- broad refactor
- public booking/payment/waitlist/handoff changes

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли файлы, которые будут добавлены/изменены
2. перечисли endpoint(s)
3. перечисли schemas/services/repository changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть protected access for move endpoint
- покрыть successful move for one conservatively eligible case
- покрыть not-found behavior
- покрыть invalid source-state handling
- покрыть invalid target-tour/boarding handling
- покрыть safe seat mutation semantics
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Новый endpoint
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed