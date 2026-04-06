Нужно выполнить documentation-only realignment pass в проекте Tours_BOT, чтобы снять проблему устаревшего checkpoint в handoff-документах.

Контекст:
Сейчас реальное состояние проекта сильно ушло вперёд по сравнению со старым содержимым `docs/CHAT_HANDOFF.md`, где ещё мог оставаться checkpoint уровня:
- Phase 5 / Step 4 completed
- Next Safe Step: Phase 5 / Step 5

Это больше не соответствует фактическому состоянию проекта.

Фактический approved checkpoint, который нужно отразить:
- Phase 6 / Step 30 completed

Фактически уже завершено в Phase 6:
- protected admin foundation
- tours narrow CRUD-like slices
- boarding point narrow CRUD-like slices
- tour translations narrow slices
- boarding point translations narrow slices
- tour archive/unarchive
- read-only admin order/payment correction visibility
- read-only admin action preview on order detail
- handoff queue/detail
- narrow handoff mutations:
  - mark-in-review
  - close
  - assign
  - reopen
- narrow admin order correction/mutation slices:
  - mark-cancelled-by-operator
  - mark-duplicate
  - mark-no-show
  - mark-ready-for-departure
- read-side lifecycle refinement:
  - ready_for_departure_paid
- move-readiness decision support
- narrow admin order move mutation
- move placement snapshot (current-state only, no persisted move timeline)

Также нужно явно зафиксировать на будущее:
- admin payment mutations intentionally postponed
- payment reconciliation remains the single source of truth for paid-state transitions
- revisit payment-side admin operations later, before:
  - real provider integration
  - refund workflow
  - production payment rollout
  - broader admin-side payment operations

Задача:
обновить только документацию:
1. `docs/CHAT_HANDOFF.md`
2. `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`

Никакой production code не менять.

Что нужно сделать:

1. Обновить `docs/CHAT_HANDOFF.md`
Нужно:
- убрать устаревшую опору на old checkpoint уровня Phase 5 / Step 4
- зафиксировать актуальный approved checkpoint:
  - `Phase 6 / Step 30 completed`
- обновить:
  - `Current Status`
  - `Current Phase`
  - `Current Architecture State`
  - `Not Implemented Yet`
  - `Next Safe Step`
  - `Recommended Next Prompt`
- убедиться, что новый handoff однозначно ведёт вперёд из текущего состояния, а не назад к старым Step 5 / Step 6 и т.п.
- явно указать, что continuity должна идти по актуальному Phase 6 checkpoint

Что должно быть отражено в `CHAT_HANDOFF.md`:
- current project state уже находится в Phase 6, не в Phase 5
- current admin surface already includes all completed Phase 6 slices listed above
- public booking/payment/waitlist/handoff flows не менялись этими admin slices
- `Next Safe Step` должен смотреть только вперёд от Step 30, а не к старым Phase 5 prompts

Для `Next Safe Step`:
- не ставить payment mutation как default next implementation
- зафиксировать более безопасное направление:
  - либо Phase 6 review / stabilization checkpoint
  - либо ещё один read-only / low-risk admin refinement
- если выбираешь между ними, предпочти:
  - `Phase 6 review / stabilization checkpoint before any admin payment mutation`

2. Обновить `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
Добавить короткий, но явный пункт про будущее payment-side admin work.

Нужно зафиксировать смысл:
- admin payment mutations are intentionally postponed
- payment reconciliation remains the single source of truth for paid-state transitions
- revisit only later, before:
  - provider-integrated payment admin operations
  - refund workflow
  - production payment rollout
  - broader admin-side payment actions

Важно:
- не раздувать документ
- не делать большой redesign текста
- просто добавить ясную future-work note в подходящее место

3. Проверить блок `## New Chat Startup Prompt`
Он должен:
- остаться один
- остаться в конце файла
- ссылаться на актуальный checkpoint
- не уводить новый чат назад к Phase 5 / Step 5
- опираться на `docs/CHAT_HANDOFF.md` как на primary checkpoint document for continuity

Жёсткие правила:
- не трогать production код
- не менять API поведение
- не менять бизнес-логику
- не добавлять новые implementation slices
- это только documentation-only alignment pass

Перед правками кратко зафиксируй:
1. текущее реальное состояние проекта
2. какая проблема в docs сейчас исправляется
3. какой checkpoint должен стать актуальным
4. что не должно меняться

После правок дай отчёт:
1. какие документы изменены
2. что именно исправлено в `docs/CHAT_HANDOFF.md`
3. какой актуальный checkpoint теперь зафиксирован
4. какой `Next Safe Step` теперь указан
5. какой payment-side future work note добавлен в `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
6. подтверждение, что это documentation-only pass
7. подтверждение, что `## New Chat Startup Prompt` остался один и в конце файла