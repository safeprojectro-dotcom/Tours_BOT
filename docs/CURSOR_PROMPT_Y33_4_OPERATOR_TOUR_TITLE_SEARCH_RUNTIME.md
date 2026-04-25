Continue Tours_BOT strict continuation.

Task:
Implement title substring search for Telegram admin compatible tour selection UI.

Read first:
- docs/CHAT_HANDOFF.md
- docs/OPERATOR_LINK_TOUR_TITLE_DATE_SEARCH_GATE.md
- docs/OPERATOR_LINK_TOUR_SEARCH_GATE.md
- docs/HANDOFF_Y33_1_OPERATOR_TOUR_SEARCH_GATE_ACCEPTED.md

Goal:
Extend existing Y33.2 code search to also search by tour title substring.

Scope:
From:
/admin_published -> offer detail -> Execution link -> Create/Replace execution link -> Search compatible tours

Current search:
- exact/partial tour code

Add:
- title_default substring search

Rules:
- keep code search behavior unchanged
- same sales_mode filter always
- future tours only
- not cancelled/completed
- no auto-linking
- no auto-create tours
- supplier_offer != tour
- no Mini App changes
- no Layer A booking/payment changes
- no identity bridge changes
- no migrations
- result selection still opens existing confirmation screen
- manual fallback remains

UX:
- Existing prompt can remain:
  "Send tour code or part of code"
  but preferably update to:
  "Send tour code or part of code/title"
- Result header should make clear this is compatible search result.
- No ranking/scoring. Stable ordering by departure_datetime then id.

Tests:
- existing code exact/partial tests still pass
- title substring returns matching compatible tour
- title substring does not return wrong sales_mode tour
- no results state still works
- selecting title result opens confirmation
- callback_data length tests still pass
- existing create/replace/status/close tests pass

After coding report:
- files changed
- exact search behavior
- tests run
- postponed items