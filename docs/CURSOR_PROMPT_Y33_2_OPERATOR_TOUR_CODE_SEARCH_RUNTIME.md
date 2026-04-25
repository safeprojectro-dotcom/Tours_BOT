Continue Tours_BOT strict continuation.

Task:
Implement first safe runtime slice for Telegram admin compatible tour search by tour code.

Read first:
- docs/CHAT_HANDOFF.md
- docs/HANDOFF_Y33_1_OPERATOR_TOUR_SEARCH_GATE_ACCEPTED.md
- docs/OPERATOR_LINK_TOUR_SEARCH_GATE.md
- docs/HANDOFF_Y32_9_OPERATOR_LINK_TOUR_SELECTION_ACCEPTED.md

Goal:
Extend Telegram admin execution-link tour selection UI with bounded search by tour code.

Scope:
From:
/admin_published -> offer detail -> Execution link -> Create/Replace execution link

Add:
- "Search compatible tours" button
- prompt for exact or partial tour code
- return compatible results filtered by:
  - same sales_mode as supplier_offer
  - existing tours only
  - code match exact/partial
- results go through existing candidate list / confirmation screen
- manual tour_id/code fallback remains

Strict rules:
- no auto-linking
- no auto-create tours
- supplier_offer != tour
- no Mini App changes
- no Layer A booking/payment changes
- no identity bridge changes
- no migrations
- direct booking CTA remains controlled by active authoritative link + linked tour policy

UX:
1. Candidate list screen shows:
   - compatible tours
   - Search compatible tours
   - Manual tour_id/code input
   - Back
2. Search prompt asks:
   "Send tour code or part of code"
3. Search results:
   - same candidate card format
   - same confirmation flow
   - clear no-results message
   - Back to compatible list
4. Callback data must remain <= 64 bytes.

Implementation:
- Prefer reusing existing FSM/input pattern from manual tour_id/code input.
- Search mode must preserve:
  - offer_id
  - action mode create/replace
- Do not store large query in callback_data.
- If query needs to be preserved, keep it in FSM state, not callback_data.

Tests:
- search button enters code-search state
- exact code match returns compatible tour
- partial code match returns compatible tour
- wrong sales_mode tour is excluded
- no results state
- selecting search result opens confirmation
- manual fallback still works
- callback_data length tests still pass
- existing create/replace/close/status tests still pass

After coding report:
- files changed
- exact UI path
- state/FSM additions
- tests run
- postponed items