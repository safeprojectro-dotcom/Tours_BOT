Continue Tours_BOT strict continuation.

Task:
Implement first safe runtime slice for Telegram admin UI create/replace supplier_offer_execution_links.

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPERATOR_LINK_CREATE_REPLACE_UI_GATE.md
- docs/HANDOFF_Y32_5_OPERATOR_EXECUTION_LINK_UI_SLICE_ACCEPTED.md
- docs/OPERATOR_EXECUTION_LINK_WORKFLOW_GATE.md

Goal:
Extend existing Telegram admin execution link UI:
- from /admin_published -> offer detail -> Execution link
- allow admin/operator to create or replace execution link using safe explicit tour selection.

Strict rules:
- no auto-create tours
- supplier_offer != tour
- no Layer A booking/payment changes
- no Mini App changes
- no identity bridge changes
- no migrations unless absolutely unavoidable
- direct booking CTA remains controlled only by active authoritative link + linked tour policy

Preferred safe UX:
1. On Execution link status screen:
   - if no active link: show "Create execution link"
   - if active link exists: show "Replace execution link" and "Close active link"
2. Tour selection:
   - first safe version may use explicit tour_id input OR paginated compatible tour list if existing admin UI supports it
   - must filter/validate same sales_mode
   - show tour id/code/title/status/sales_mode/seats
3. Confirmation screen:
   - show offer id/title/sales_mode
   - show target tour id/code/sales_mode/status/seats
   - warn: Mini App CTA appears only if linked tour is bookable
4. Create/replace:
   - call existing service/API logic
   - create if no active link
   - replace if active link exists
   - after success show updated status/history

Validation:
- supplier_offer exists
- tour exists
- sales_mode matches
- cannot create duplicate active link
- replace closes previous active link
- invalid target -> clear admin message, no state change

Tests:
- create link callback/input flow
- replace link flow closes old active link
- sales_mode mismatch is blocked with admin-visible message
- no Mini App behavior changes
- existing close/status tests still pass

After coding report:
- files changed
- UI path implemented
- create/replace exact behavior
- tests run
- postponed items