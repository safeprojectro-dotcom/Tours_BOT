Нужно сделать documentation-only recovery note после production incident в проекте Tours_BOT.

Контекст:
После Phase 6 / Step 6 backend code with new ORM field `tours.cover_media_reference` был задеплоен в Railway, но migration в production Postgres ещё не была применена.
Из-за этого production backend начал падать на чтении туров с ошибкой:

- `sqlalchemy.exc.ProgrammingError`
- `psycopg.errors.UndefinedColumn`
- `column tours.cover_media_reference does not exist`

Фактический эффект:
- `/mini-app/catalog` → 500
- `/mini-app/bookings` initially failed / became unavailable for normal usage until recovery
- Mini App visually showed loading failure
- root cause was production schema mismatch, not Mini App UI logic

Recovery, который реально сработал:
1. определить, что Railway DB schema отстаёт от deployed code
2. взять public Postgres URL for Railway DB
3. локально временно задать `DATABASE_URL` на public Railway Postgres URL
4. использовать driver-explicit URL:
   `postgresql+psycopg://...`
5. запустить:
   - `.\.venv\Scripts\python.exe -m alembic current`
   - `.\.venv\Scripts\python.exe -m alembic upgrade head`
6. после применения миграции сделать Redeploy сервиса `Tours_BOT`
7. перепроверить:
   - `/health`
   - `/mini-app/catalog`
   - `/mini-app/bookings`
8. убедиться, что 500 ушли и catalog/bookings снова работают

Что нужно сделать:

1. Обновить `docs/OPEN_QUESTIONS_AND_TECH_DEBT.md`
Добавить новую короткую секцию про operational deployment risk, например в конце документа.

Смысл новой записи:
- Railway production deploy can break if Alembic migration is not applied before/alongside code using new columns
- `railway shell` alone is not enough for internal DB access from local machine because internal hostnames like `*.railway.internal` are not resolvable locally
- recovery path may require using Railway public Postgres URL temporarily with:
  - `DATABASE_URL=postgresql+psycopg://...`
  - local alembic against Railway DB
- after migration, backend redeploy and smoke-check are required
- this is especially important for Mini App/catalog/order paths that read changed ORM fields

Добавь для этой записи:
- Current decision / current lesson
- Why accepted now
- Risk later
- Revisit trigger
- Status: open

Хорошая формулировка риска:
`Production schema may lag behind deployed code when Alembic migrations are not applied as part of release flow.`

Хорошая формулировка revisit trigger:
- before next schema-changing deploy
- before release checklist is considered complete
- before production rollout automation is treated as stable

2. Обновить `docs/CHAT_HANDOFF.md`
Добавить короткую operational note, не раздувая handoff.

Нужно кратко зафиксировать:
- after Step 6 there was a production schema mismatch on `tours.cover_media_reference`
- recovery was completed successfully
- production catalog/bookings recovered after applying Alembic migration and redeploy
- future schema-changing steps must include:
  - migration apply
  - redeploy
  - smoke-check for affected routes

Это не должен быть длинный incident report.
Это должна быть короткая, practical continuity note for the next chat.

3. Ничего не менять в production code
- no code edits
- no API changes
- no new feature work
- documentation-only pass

Перед правками кратко зафиксируй:
1. текущее состояние проекта
2. что произошло
3. как был выполнен recovery
4. что не должно меняться в этом pass

После правок дай отчёт:
1. какие документы изменены
2. какой новый tech-debt / ops-risk note добавлен в `OPEN_QUESTIONS_AND_TECH_DEBT.md`
3. какая короткая continuity note добавлена в `CHAT_HANDOFF.md`
4. подтверждение, что это documentation-only pass без изменений business logic