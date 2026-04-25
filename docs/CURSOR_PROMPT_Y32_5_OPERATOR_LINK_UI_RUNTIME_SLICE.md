Continue Tours_BOT strict continuation.

Task:
Implement first safe runtime slice for Telegram/admin operator UI to manage supplier_offer_execution_links.

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPERATOR_EXECUTION_LINK_UI_GATE.md
- docs/OPERATOR_EXECUTION_LINK_WORKFLOW_GATE.md
- docs/SUPPLIER_CONVERSION_BRIDGE_IMPLEMENTATION_GATE.md

Goal:
Give central admin/operator a Telegram/admin workflow to inspect and manage execution links without using raw API manually.

Scope:
1. Show supplier offer execution link status.
2. Show active link if exists.
3. Show link history.
4. Allow close active link.
5. Optionally allow create/replace link only if existing admin UI has safe tour selection pattern.

Strict rules:
- no auto-create tours
- no supplier_offer == tour
- no Layer A booking/payment changes
- no identity bridge changes
- no Mini App behavior changes
- no migrations unless absolutely necessary
- direct booking CTA remains controlled by existing read-side resolver

Preferred first safe slice:
- read/status + close active link first
- create/replace only if validation and tour selection are already safe

Validation:
- admin only
- supplier_offer must exist
- active link must exist for close
- close must leave no active link

Tests:
- focused unit tests for callback/handler/service wiring
- existing supplier execution link service tests remain passing

After coding report:
- files changed
- UI entry point
- actions implemented
- tests run
- what remains postponed