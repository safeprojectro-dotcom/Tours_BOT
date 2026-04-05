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
- Phase 6 / Steps 1–4 completed:
  - protected admin foundation
  - read-only overview / tours / orders
  - list/detail/filter visibility
- Phase 6 / Step 5 completed:
  - POST /admin/tours
- Phase 6 / Step 6 completed:
  - PUT /admin/tours/{tour_id}/cover
- Phase 6 / Step 7 completed:
  - PATCH /admin/tours/{tour_id}
- Phase 6 / Step 8 completed:
  - POST /admin/tours/{tour_id}/boarding-points
- Phase 6 / Step 9 completed:
  - PATCH /admin/boarding-points/{boarding_point_id}
- Phase 6 / Step 10 completed:
  - DELETE /admin/boarding-points/{boarding_point_id}
- Phase 6 / Step 11 completed:
  - PUT /admin/tours/{tour_id}/translations/{language_code}
- Phase 6 / Step 12 completed:
  - DELETE /admin/tours/{tour_id}/translations/{language_code}
- Phase 6 / Step 13 completed:
  - PUT /admin/boarding-points/{boarding_point_id}/translations/{language_code}
- Phase 6 / Step 14 completed:
  - DELETE /admin/boarding-points/{boarding_point_id}/translations/{language_code}
- Phase 6 / Step 15 completed:
  - POST /admin/tours/{tour_id}/archive
  - POST /admin/tours/{tour_id}/unarchive
- admin read-side is established
- narrow admin write slices for tours, boarding points, translations, and archive/unarchive now exist
- public flows must remain untouched

Текущая задача:
Phase 6 / Step 16

Нужен только один узкий safe slice:
NARROW ADMIN ORDER / PAYMENT CORRECTION VISIBILITY SLICE

Что именно сделать:
1. Добавить только read-only admin visibility enhancement for order/payment correction context.
Предпочтительный узкий вариант:
   - расширить `GET /admin/orders/{order_id}`
   - и/или very small companion read endpoint if absolutely necessary
Но по умолчанию предпочитай расширение уже существующего detail endpoint, без новых мутаций.

2. Цель шага:
- дать админу более явную visibility по тому,
  - какие payment entries связаны с заказом,
  - какой payment state сейчас primary/admin-visible,
  - есть ли correction-relevant ambiguity,
  - нужен ли ручной операторский разбор
- не открывать пока реальные order/payment mutations

3. Что именно показать в read-side:
- current order lifecycle_kind / lifecycle_summary remains primary
- payment records summary stays visible
- добавить very narrow correction-oriented fields, только если они реально полезны и grounded in existing data:
  - `payment_correction_hint`
  - `needs_manual_review`
  - `payment_records_count`
  - `latest_payment_status`
  - `latest_payment_provider`
  - `latest_payment_created_at`
  - `has_multiple_payment_entries`
  - `has_paid_entry`
  - `has_awaiting_payment_entry`
  - similar very small computed fields if supported by current model
- do not invent broad reporting structures

4. Validation / safety rules:
- read-only only
- no mutation of order/payment/handoff state
- no reconciliation rewrite
- no webhook behavior change
- no public booking/payment flow changes
- any computed hint must be conservative and explainable from current persisted data
- if hint logic is introduced, keep it clearly secondary to existing lifecycle logic

5. Service-layer rules:
- keep repositories persistence-oriented only
- keep interpretation/computed hint logic in service layer
- route layer thin
- do not spread correction semantics into frontend/public code

6. Response shape:
- extend existing `AdminOrderDetailRead` narrowly
- avoid new parallel admin detail model unless absolutely necessary

Очень важно:
- do not add order mutation in this step
- do not add payment mutation/refund/capture in this step
- do not add reconciliation command endpoints
- do not widen into operator workflow engine
- do not change current lifecycle semantics as the primary admin meaning
- do not touch public payment flow

Разрешённый scope:
- narrow read-only visibility enhancement around correction context
- minimal schema/service/repository expansion needed for this
- focused tests only

Запрещено в этом шаге:
- order status mutation
- payment mutation
- refund / capture / cancel payment actions
- webhook changes
- reconciliation logic rewrite
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
- покрыть successful detail read with new correction-oriented fields
- покрыть order not found behavior
- покрыть at least one case with multiple payment entries if supported by current fixtures/model
- покрыть conservative hint/manual-review logic if introduced
- не переписывать старые test slices без причины

После реализации дай отчёт:
1. Изменённые файлы
2. Что реализовано
3. Какие endpoint/model changes добавлены
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed