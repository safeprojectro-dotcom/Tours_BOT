# HANDOFF_Y33_6_SEARCH_NO_RESULTS_AND_FSM_FIX_ACCEPTED

## Scope
Y33.6 + Y33.6A — no-results UX and FSM routing fix for Telegram admin execution-link tour search.

## Accepted behavior
- Empty search results show a clear no-results message.
- The response includes searched value.
- It confirms no execution link was changed.
- It suggests removing date, using a shorter query, or using manual tour_id/code input.
- Buttons shown:
  - Back to compatible list
  - Manual tour_id/code input
  - Back

## FSM fix
A regression was observed where search input messages were not handled after entering the search prompt.

Manual smoke confirmed the fixed behavior:
- `zzzz 2026-06-16` returns no-results UX.
- `2026-06-16` returns compatible tour #3.
- Search remains limited to compatible tours.

## Safety preserved
- No search logic changes beyond routing/state fix.
- No filter changes.
- No execution-link semantics changes.
- No Mini App changes.
- No Layer A booking/payment changes.
- No identity bridge changes.
- No migrations.
- Callback payloads remain compact.

## Status
ACCEPTED — safe to proceed after committing cleanup and handoff.