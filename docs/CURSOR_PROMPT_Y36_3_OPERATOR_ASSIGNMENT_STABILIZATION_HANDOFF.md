Continue Tours_BOT from Y36.2 / Y36.2A.

Goal:
Create a docs-only stabilization checkpoint after operator assignment runtime implementation and the production ORM mapper fix.

Scope:
1. Update docs/CHAT_HANDOFF.md.
2. Update docs/OPEN_QUESTIONS_AND_TECH_DEBT.md if needed.
3. Do not change runtime code, migrations, API, Telegram handlers, Mini App, booking/payment, supplier routes, execution links, or identity bridge.

Must document:
- Y36.2 Assign to me implemented for custom marketplace requests.
- Migration 20260429_18 added assigned_operator_id, assigned_by_user_id, assigned_at.
- Production migration was applied on Railway via railway ssh:
  - python -m alembic upgrade head
  - python -m alembic current
- Y36.2A fixed SQLAlchemy mapper crash:
  - CustomMarketplaceRequest.assigned_operator relationship required User.ops_assigned_custom_marketplace_requests.
  - assigned_by side now has symmetric back_populates.
  - configure_mappers smoke test added.
- Production smoke result:
  - bot recovered after deploy
  - /admin_requests works
  - request detail shows Owner
  - Assign to me changes Owner to Assigned to you
- Tests confirmed:
  - python -m compileall app tests/unit/test_api_admin.py tests/unit/test_telegram_admin_moderation_y281.py
  - python -m pytest tests/unit/test_api_admin.py -k "assign" -> 21 passed
  - python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -k "admin_ops" -> 4 passed

Next safe pointer:
- Continue with Y36.4 only after this docs checkpoint is committed.
- Y36.4 may be operator assignment UI polish/filtering, but no reassign/unassign yet unless separately gated.

Verification:
- git diff -- docs/CHAT_HANDOFF.md docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- confirm docs-only changes.