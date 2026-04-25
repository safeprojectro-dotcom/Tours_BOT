Continue Tours_BOT after Y36.4 production smoke.

Task:
Create docs-only acceptance checkpoint for Y36.2/Y36.2A/Y36.4 operator assignment.

Scope:
- docs/CHAT_HANDOFF.md
- optionally docs/OPEN_QUESTIONS_AND_TECH_DEBT.md

Do not change runtime code, migrations, API, Telegram handlers, Mini App, booking/payment, supplier routes, execution links, or identity bridge.

Record accepted state:
- Y36.2 Assign to me implemented for custom marketplace requests.
- Migration 20260429_18 applied in Railway production.
- Assignment stores users.id via assigned_operator_id / assigned_by_user_id, not raw Telegram id.
- Request lifecycle/status remains unchanged by assignment.
- Y36.2A fixed SQLAlchemy mapper crash with symmetric User <-> CustomMarketplaceRequest relationships.
- Mapper smoke test exists.
- Y36.4 Telegram UI polish accepted:
  - list shows Owner early
  - unassigned owner is —
  - assigned-to-current-operator shows you / Assigned to you
  - Assign to me hidden after assignment
- Production smoke passed:
  - /admin_requests works
  - detail shows Owner
  - Assign to me changes Owner to Assigned to you
  - Railway logs show webhook 200 and no mapper errors

Record tests:
- python -m compileall app tests/unit/test_api_admin.py tests/unit/test_telegram_admin_moderation_y281.py
- python -m pytest tests/unit/test_api_admin.py -k "assign" -> 21 passed
- python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -k "admin_ops" -> 4/8 passed depending on local slice
- Y36.4 focused admin_ops tests -> 8 passed

Next safe pointer:
- Next step should be a design gate before any reassign/unassign/resolve/close.
- Recommended next: Y37 operator request workflow gate OR Y36.6 small formatting polish for request dates/customer summary.
- Do not implement reassign/unassign without separate gate.

Verification:
- git diff -- docs/CHAT_HANDOFF.md docs/OPEN_QUESTIONS_AND_TECH_DEBT.md
- confirm docs-only scope.