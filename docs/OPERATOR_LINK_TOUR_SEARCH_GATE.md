# Operator Link Tour Search Gate

## 1) Current accepted state
- Y32.9 accepted Telegram admin execution-link tour selection:
  - `/admin_published` -> offer detail -> `Execution link` -> create/replace flow;
  - compatible tour list works for create and replace;
  - candidate selection opens the existing confirmation screen;
  - confirm replace closes the previous active link as `replaced`;
  - exactly one active link remains;
  - manual `tour_id` / exact tour-code fallback remains available.
- Compatible list filters by `supplier_offer.sales_mode`.
- Candidate cards show tour id, code, title, status, `sales_mode`, departure, seats, and Mini App CTA warning.
- `BUTTON_DATA_INVALID` regression is fixed by compact callback payloads:
  - `el:list:{offer_id}:{mode}:{page}`;
  - `el:pick:{offer_id}:{mode}:{tour_id}`;
  - `el:manual:{offer_id}:{mode}`.
- Current postponed item: bounded search/refinement by tour code, title, and optional date hint.
- This gate is docs-only. It does not change runtime code, migrations, Mini App, Layer A booking/payment, identity bridge, or API semantics.

## 2) Why search is needed
- A paginated compatible list is safe, but operators still need faster narrowing when many same-`sales_mode` tours exist.
- Search reduces operational friction when the operator knows:
  - part of a tour code;
  - a title fragment;
  - an approximate departure date.
- Search must remain refinement only:
  - it narrows compatible candidates;
  - it does not infer the target;
  - it does not auto-link;
  - it still requires explicit selection and confirmation.

## 3) Search input UX
- Entry point:
  - compatible tour list screen adds `Search compatible tours`.
- Search prompt:
  - ask for a bounded query;
  - examples: `ABC`, `Weekend`, `2026-09-01`;
  - explain that search still filters by compatible `sales_mode`.
- Controls should include:
  - `Back to compatible list`;
  - `Manual tour_id/code input`;
  - `Back to link status`;
  - `Home`.
- Search state must preserve:
  - offer id;
  - create vs replace mode;
  - query text;
  - optional parsed date;
  - page.
- Search should not interrupt the existing manual fallback path.

## 4) Supported search fields
- Tour code:
  - exact code match;
  - partial code match;
  - case-insensitive where supported safely by the DB dialect.
- Tour title:
  - substring match against default title;
  - case-insensitive where supported safely by the DB dialect.
- Date hint/filter:
  - `YYYY-MM-DD`;
  - filters or prioritizes tours departing on that date;
  - invalid date input returns a clear admin-visible message and no mutation.
- Out of scope for this gate:
  - fuzzy matching;
  - supplier-offer text matching heuristics;
  - price matching;
  - customer/order/payment search.

## 5) Filtering and compatibility rules
- Search must always apply the same hard compatibility filters as the base candidate list:
  - existing Layer A `tour` only;
  - same `sales_mode` as the supplier offer;
  - not cancelled;
  - not completed;
  - future departure.
- Search results must remain admin/operator-only.
- Search must not expose:
  - customer PII;
  - order/customer lists;
  - payment provider data;
  - supplier-private data beyond existing admin permissions.
- Service-layer validation remains authoritative at selection/confirmation/mutation time.
- A search result becoming stale must fail closed at confirmation or service validation.

## 6) Result card format
Result cards should reuse the compatible-list card format:

```text
Tour #3 (FULL-BUS-01)
Weekend Full Bus | status: open_for_sale | sales_mode: full_bus
Departure: 2026-09-01 08:00 | Seats: 0/40
CTA: not guaranteed; Mini App enables direct booking only if linked tour is bookable.
```

Additional search context may be shown above the results:

```text
Search: "FULL-BUS" | page 1
```

Selection button:

- `Select tour #3`

The result card must not place tour title/code/status in `callback_data`; those belong only in visible text.

## 7) Pagination/search-state rules
- Page size should match the compatible list:
  - recommended: 5 results per page.
- Ordering should remain stable:
  - future departures first;
  - earlier departure first;
  - tour id ascending.
- Pagination must preserve:
  - offer id;
  - create/replace mode;
  - search query;
  - optional date filter;
  - page.
- Callback payloads must stay compact and under Telegram's 64-byte limit.
- Search pagination should use compact opaque or abbreviated payloads when needed; do not include long query text directly in callback data if it risks the limit.
- If query text cannot fit safely into callbacks, store it in FSM state and keep callback data to ids/mode/page only.

## 8) Fail-safe behavior
- No query entered means no mutation.
- Invalid date means no mutation.
- No results means no mutation and shows a clear message.
- Search result selection still opens confirmation; it never mutates directly.
- If selected tour fails compatibility after search, show a clear admin message and keep existing active link unchanged.
- Create still blocks if an active link exists.
- Replace still blocks if no active link exists.
- Manual `tour_id` / exact tour-code input remains available.
- No search path may create, clone, modify, or infer tours.
- No search path may mutate Layer A booking, reservations, payments, RFQ state, Mini App, or identity bridge.

## 9) Tests required
- Search by code:
  - exact code returns matching compatible tours;
  - partial code narrows results;
  - mismatched `sales_mode` tours stay hidden.
- Search by title:
  - title substring returns matching compatible tours;
  - cancelled/completed/past tours stay hidden.
- Date hint/filter:
  - valid `YYYY-MM-DD` narrows or prioritizes that departure date;
  - invalid date shows clear message and no mutation.
- Search result flow:
  - selecting a result opens the existing confirmation screen;
  - create from selected result creates one active link;
  - replace from selected result closes the old link as `replaced`.
- Pagination/search-state:
  - next/prev preserves offer id, mode, query/date context, and page;
  - callback data remains under 64 UTF-8 bytes.
- Regressions:
  - compatible base list still works;
  - manual fallback still works;
  - `sales_mode` mismatch guard still blocks with no state change;
  - close/status/history still work;
  - Mini App supplier-offer landing behavior remains unchanged.

## 10) First safe runtime slice recommendation
- Implement search in small runtime slices:
  1. exact/partial tour-code search only;
  2. title substring search;
  3. optional date hint/filter.
- Start with code search because it is the least ambiguous and closest to the already accepted exact-code manual fallback.
- Keep search state in FSM if callback payload length might exceed Telegram limits.
- Keep compact callback payloads and add tests asserting all generated callback data is `<= 64` UTF-8 bytes.
- Reuse existing candidate card, selection, confirmation, and service-layer mutation paths.
- Do not add migrations.
- Do not add Mini App logic.
- Do not add auto-tour creation.
