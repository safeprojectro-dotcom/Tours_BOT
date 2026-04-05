Продолжаем этот же проект: Tours_BOT.

**Статус checkpoint (архив промпта):** **Phase 6 / Step 1 — реализован** в коде (см. `docs/CHAT_HANDOFF.md`, секция **Completed Steps → Phase 6**). Для **новой** работы используй актуальный **Next Safe Step** в `docs/CHAT_HANDOFF.md` (сейчас — Phase 6 / Step 2).

Работай как продолжение предыдущего approved checkpoint, без потери контекста, без возврата к уже закрытым Phase 1–5 шагам и без расширения scope.

Сначала используй как source of truth:
1. docs/IMPLEMENTATION_PLAN.md
2. docs/CHAT_HANDOFF.md
3. docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
4. docs/PHASE_5_ACCEPTANCE_SUMMARY.md
5. docs/MINI_APP_UX.md
6. docs/TESTING_STRATEGY.md
7. docs/AI_ASSISTANT_SPEC.md
8. docs/AI_DIALOG_FLOWS.md
9. docs/TECH_SPEC_TOURS_BOT.md

Контекст продолжения:
- Phase 5 (Mini App MVP) уже принят для MVP/staging
- Step 20 был documentation-only consolidation/acceptance pass
- booking, payment mock completion, waitlist MVP, handoff entry, ops queue visibility, handoff ops actions, waitlist ops actions, waitlist user visibility polish, My bookings grouping/history compaction, Telegram chat cleanup, support text unification уже считаются завершёнными и не должны переоткрываться
- следующий большой этап по плану: Phase 6 — Admin Panel MVP

Жёсткие правила:
- не повторять уже завершённую работу
- не откатывать принятые архитектурные решения
- не расширять scope без необходимости
- продолжать только от последнего approved checkpoint
- сохранять архитектуру: bot layer / api / services / repositories / mini_app / internal ops
- не переносить business logic во frontend
- PostgreSQL-first
- все изменения делать маленьким безопасным вертикальным срезом
- route layer должен оставаться thin
- repositories — только persistence/data access
- services — владеют business rules и orchestration
- не менять public booking/payment/waitlist/handoff user flows в этом шаге

Текущая задача:
Начать Phase 6 / Step 1.

Нужен только один узкий safe slice:
PROTECTED ADMIN FOUNDATION + MINIMAL READ-ONLY ADMIN VISIBILITY

Что именно нужно сделать в этом шаге:
1. Добавить минимальный protected admin foundation на backend стороне
2. Добавить базовый admin access/auth dependency layer
3. Добавить protected admin API router
4. Добавить только минимальные read-only admin endpoints
5. Дать минимальную operational visibility без CRUD и без full admin SPA

Разрешённый scope этого шага:
- admin auth/access baseline
- protected admin API foundation
- read-only admin overview / visibility
- read-only tours visibility
- read-only orders visibility
- при необходимости read-only summary по handoff/waitlist/payment state на overview уровне, только если это можно безопасно собрать из существующих сервисов/репозиториев
- focused tests только на новый protected access и read-only endpoints

Запрещено в этом шаге:
- большой SPA
- full admin UI
- full CRUD tours
- translations CRUD
- boarding points CRUD
- manual order/payment mutations
- admin payment operations
- publication/content workflows
- изменение public booking/payment flows
- перенос логики в frontend
- новый waitlist workflow
- новый handoff workflow
- любые широкие refactor-волны

Очень важно:
В docs/OPEN_QUESTIONS_AND_TECH_DEBT.md уже зафиксирован риск, что текущая expiry semantics может быть неправильно интерпретирована в admin views:
- booking_status может оставаться reserved
- payment_status становится unpaid
- cancellation_status становится cancelled_no_payment
Поэтому в admin read models / summaries сразу сделай безопасное human-readable представление состояний, чтобы admin visibility не показывала двусмысленные raw combinations как будто бронь ещё активна.

Ожидаемый результат этого шага:
- существует защищённая admin entry point
- существует минимальный protected admin router
- admin может получить read-only operational visibility
- есть read-only tours list
- есть read-only orders list
- статусы в admin read модели интерпретируются безопасно и понятно
- public flows не изменены

Перед кодом сначала кратко зафиксируй:
1. текущее состояние проекта
2. что уже завершено
3. какой exact next safe step
4. что сейчас трогать нельзя

Потом:
1. перечисли, какие файлы планируешь добавить/изменить
2. перечисли новые endpoints
3. перечисли новые/расширенные schemas/services/dependencies
4. отдельно перечисли, что останется out of scope после этого шага

После этого — только затем — генерируй код.

Требования к реализации:
- backend-first
- минимальные изменения
- reuse existing repositories/services where possible
- new logic only where needed for admin read-side
- no duplicated business logic
- no raw status leakage in admin read DTOs where it creates ambiguity
- keep code production-oriented and narrow

Требования к тестам:
- добавить только focused tests
- покрыть protected admin access
- покрыть read-only admin endpoints
- покрыть human-readable status projection for expired/unpaid reservation cases
- не переписывать старые test slices без причины

После реализации дай отчёт в формате:
1. Изменённые файлы
2. Что реализовано
3. Новые endpoints
4. Какие тесты запущены
5. Результаты
6. Что осталось out of scope / postponed