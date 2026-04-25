# HANDOFF_Y33_1_OPERATOR_TOUR_SEARCH_GATE_ACCEPTED

## Scope
Y33.1 — Design gate for bounded search/refinement in Telegram admin tour selection.

## What was done
Created docs/OPERATOR_LINK_TOUR_SEARCH_GATE.md.

Defined bounded search UX for operator tour selection:
- search by tour code (exact/partial)
- search by title substring
- optional date hint/filter
- always constrained by same sales_mode

## Design principles confirmed
- supplier_offer != tour
- no auto-linking from search
- search is refinement only, not authority
- confirmation screen remains mandatory before create/replace
- fail-closed behavior preserved
- manual fallback remains available

## Search constraints
- same sales_mode only
- existing tours only
- future/not cancelled/completed
- no implicit matching or auto-selection

## UX decisions
- explicit "Search compatible tours" action
- bounded query input (text/date)
- result list uses same card format as compatible list
- pagination preserves search context
- selection always goes through confirmation

## Safety guarantees
- no mutation without explicit confirmation
- stale/invalid results revalidated before execution
- no changes to:
  - Mini App
  - Layer A booking/payment
  - identity bridge
  - execution link semantics

## Postponed
- advanced filtering
- multi-field search combinations
- ranking/scoring logic

## Status
ACCEPTED — safe to proceed to Y33.2 runtime (code search first).