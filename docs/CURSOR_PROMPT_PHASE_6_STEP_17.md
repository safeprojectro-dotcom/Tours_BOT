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
  - read-only overview / tours / orders
  - tour create / cover / patch / archive-unarchive
  - boarding point create / patch / delete
  - tour translation upsert / delete
  - boarding point translation upsert / delete
- Phase 6 / Step 16 completed:
  - narrow read-only admin order/payment correction visibility via GET /admin/orders/{order_id}
- admin read-side is established
- narrow admin write slices for tours, boarding points, and translations exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 17

Нужен только один узкий safe slice:
FIRST NARROW ADMIN ORDER / PAYMENT ACTIONS PREVIEW SLICE

Важно:
это НЕ реальные payment mutations.
Это только very narrow operator-ready admin visibility on what action would be appropriate next.

Что именно сделать:
1. Extend read-only admin order detail minimally, without adding mutation endpoints.
2. Add one very small computed read-only field (or a tiny group of fields) to `GET /admin/orders/{order_id}` such as:
   - `suggested_admin_action`
   - `allowed_admin_actions`
   - `payment_action_preview`
Choose the narrowest shape that fits the current data model.

3. Goal:
- help admin/operator understand what kind of manual follow-up may be appropriate
- do not perform any action
- do not alter order/payment state
- do not open a workflow engine

4. The action preview must be conservative and grounded only in existing persisted data:
- order lifecycle
- payment visibility fields already introduced
- handoff/payment ambiguity signals if already present in current detail model
- no speculative behavior
- if unsure, prefer `manual_review` / `none`

5. Keep existing lifecycle_kind / lifecycle_summary as primary.
New preview fields must remain secondary guidance only.

6. Keep route layer thin
7. Keep interpretation logic in service layer
8. Keep repositories persistence-oriented only

Очень важно:
- do not add any order mutation endpoint in this step
- do not add payment mutation/refund/capture/cancel actions
- do not add reconciliation command endpoints
- do not widen into operator workflow engine
- do not touch public payment flow
- do not change webhook behavior

Разрешённый scope:
- narrow read-only preview/guidance enhancement on existing admin order detail
- minimal schema/service changes
- focused tests only

Запрещено в этом шаге:
- order mutation
- payment mutation
- refund / capture / cancel actions
- reconciliation rewrite
- webhooks
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
2. перечисли endpoint/model changes
3. перечисли schemas/services/repository changes
4. отдельно перечисли, что остаётся out of scope

После этого — только затем — генерируй код.

Требования к тестам:
- focused tests only
- покрыть protected access for affected admin detail endpoint
- покрыть successful detail read with new preview/guidance field(s)
- покрыть order not found behavior
- покрыть at least one ambiguous payment case
- покрыть at least one clean/no-action-needed case
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие endpoint/model changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed