Continue Tours_BOT after Y36.3 stabilization.

Implement Y36.4: Telegram admin/operator assignment UI polish for custom requests.

Scope:
- Telegram admin UI only.
- Improve /admin_requests list and request detail readability around owner/assignment.
- No DB migration.
- No API semantics change.
- No reassign.
- No unassign.
- No lifecycle/status changes.

Required UI changes:
1. In /admin_requests list:
   - show owner compactly:
     - Owner: —
     - Owner: you
     - Owner: <operator summary>
   - keep customer summary visible.
   - keep rows compact enough for Telegram.

2. In request detail:
   - keep Owner line.
   - if unassigned: show Assign to me button.
   - if assigned to current operator: show Assigned to you text/state and no Assign button.
   - if assigned to another operator: show assigned operator summary and no Assign button.

3. Button/callback safety:
   - keep callback_data compact.
   - do not put PII in callback_data.

4. Tests:
   - update/add Telegram admin ops tests for:
     - unassigned request shows Assign to me
     - assigned-to-me hides Assign to me and shows Assigned to you
     - assigned-to-other hides Assign to me and shows owner summary
     - callbacks stay under Telegram 64-byte limit if there is an existing helper/test pattern

Do not touch:
- Mini App
- booking/payment
- supplier routes
- execution links
- identity bridge
- migration files
- assign-to-me API semantics

Run:
python -m compileall app tests/unit/test_telegram_admin_moderation_y281.py
python -m pytest tests/unit/test_telegram_admin_moderation_y281.py -k "admin_ops"
python -m pytest tests/unit/test_api_admin.py -k "assign"

After implementation stop and report:
- exact UI text changes
- files changed
- tests run
- confirm no migration/API/payment/Mini App changes