# HANDOFF_Y33_OPERATOR_LINK_SEARCH_ACCEPTED

## Scope
Y33 — Telegram admin compatible tour search for `supplier_offer_execution_links`.

This handoff consolidates accepted behavior from:
- Y33.2 code search;
- Y33.4 title search;
- Y33.5 `YYYY-MM-DD` date hint filter;
- Y33.6 no-results UX;
- Y33.6A FSM routing fix for search input not handled.

## Current Accepted Behavior
Telegram admin execution-link tour search is accepted in:

`/admin_published -> offer detail -> Execution link -> Create/Replace execution link -> Search compatible tours`

The operator can search compatible existing tours, select a result, and continue through the existing confirmation screen before create/replace execution-link mutation.

Search remains refinement only:
- no auto-linking;
- no auto-selection;
- no auto-tour creation;
- no direct mutation from search results.

## Supported Inputs
Search supports:
- tour code;
- tour title substring;
- `YYYY-MM-DD` date hint/filter;
- code/title + `YYYY-MM-DD` date together.

Examples:
- `SMOKE`;
- `full bus`;
- `2026-06-16`;
- `SMOKE 2026-06-16`;
- `full bus 2026-06-16`.

Date parsing is intentionally bounded:
- only `YYYY-MM-DD`;
- no fuzzy dates;
- no ranges;
- no locale date formats.

## Compatibility Filters Preserved
All search modes preserve the compatible-tour filters:
- same `sales_mode` as the supplier offer;
- existing Layer A `tour` only;
- future departure;
- not cancelled;
- not completed.

Search results remain admin/operator-only.

## No-Results UX
Empty search results now show:
- clear no-results message;
- searched value;
- confirmation that no execution link was changed;
- guidance to remove date, use a shorter query, or use manual `tour_id/code` input.

No-results buttons:
- `Back to compatible list`;
- `Manual tour_id/code input`;
- `Back`.

## Confirmation Flow Preserved
Search result selection reuses the existing candidate selection path.

Before any create/replace mutation, the existing confirmation screen still shows:
- offer context;
- target tour id/code/title;
- target tour status;
- `sales_mode`;
- seats;
- Mini App CTA warning.

The existing service validation remains authoritative before mutation.

## Callback And FSM Safety
- Callback payloads remain compact.
- Search query and optional date are stored in FSM state, not callback data.
- Search pagination preserves offer id, create/replace mode, query/date context, and page safely.
- Y33.6A manual smoke confirmed search input messages are handled by FSM after the search prompt.

## Manual Smoke Evidence
Manual smoke confirmed:
- `zzzz 2026-06-16` returns no-results UX;
- no execution link is changed in the no-results case;
- date-only `2026-06-16` returns compatible tour `#3`;
- search remains limited to compatible tours.

## Safety Preserved
No changes were made to:
- Mini App behavior;
- Layer A booking/payment;
- identity bridge;
- migrations;
- execution-link semantics;
- direct booking CTA rules.

Direct booking CTA remains controlled only by active authoritative execution link plus linked-tour bookability.

## Postponed
- Fuzzy search.
- Ranking/scoring.
- Advanced filters.
- Multi-field search combinations beyond the accepted bounded query/date form.
- Richer i18n copy polish.

## Next Safe Step Recommendation
Proceed only with operational polish that preserves the accepted Y33 boundaries:
- i18n copy refinement;
- additional admin-help text;
- larger candidate-list stress testing;
- optional docs/test cleanup.

Do not broaden search semantics, ranking, or filters without a new design gate.

## Status
ACCEPTED — Y33 operator execution-link tour search is complete and safe to build on.
