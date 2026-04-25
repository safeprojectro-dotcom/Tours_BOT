# Operator Link Tour Title/Date Search Gate

## 1) Current accepted state
- Y32.9 compatible tour selection is accepted:
  - Telegram admin create/replace execution-link flow shows compatible tour candidates;
  - candidates are filtered by `supplier_offer.sales_mode`;
  - candidate selection opens the existing confirmation screen;
  - manual `tour_id` / exact tour-code fallback remains available;
  - compact `el:*` callbacks keep Telegram `callback_data` under the 64-byte limit.
- Y33.1 bounded search/refinement gate is accepted:
  - search is refinement only;
  - search must never auto-link, auto-select, or auto-create tours;
  - selected results still go through confirmation.
- Y33.2 runtime code search is accepted:
  - exact and partial tour-code search works;
  - results remain same-`sales_mode` compatible;
  - search result selection reuses the existing confirmation flow;
  - manual fallback remains.
- This gate is docs-only. It does not change runtime code, migrations, Mini App, Layer A booking/payment, identity bridge, execution-link semantics, or API behavior.

## 2) Why title/date search is needed
- Code search is safe and precise, but operators may not always know the tour code.
- Title search helps when the operator knows the commercial route/theme name instead of the code.
- Date hints help when several similarly named tours exist across different departures.
- Title/date refinement should reduce wrong selections without increasing authority:
  - search narrows candidates;
  - search does not decide the target;
  - explicit selection and confirmation remain mandatory.

## 3) Supported input formats
- Keep existing code search unchanged.
- Supported additional inputs:
  - title substring: `Weekend`, `Chisinau`, `full bus`;
  - date hint/filter: `YYYY-MM-DD`;
  - combined lightweight input may be allowed later, for example `Weekend 2026-09-01`, but should not be the first runtime slice.
- Invalid date formats must not be guessed.
- Empty input must not mutate anything and should show a clear prompt/no-results style message.

## 4) Search interpretation rules
- Code search remains first-class and unchanged:
  - exact/partial code match continues to work as accepted in Y33.2.
- Title search:
  - match against `Tour.title_default`;
  - substring match;
  - case-insensitive where safely supported by the DB dialect;
  - no fuzzy matching in the first title slice.
- Date hint/filter:
  - parse only `YYYY-MM-DD`;
  - match tours whose `departure_datetime` falls on that date;
  - invalid date returns a clear admin-visible message and no mutation.
- If a query could be both text and date, exact `YYYY-MM-DD` is interpreted as date.
- Multi-field combined parsing is postponed unless a later gate approves it.

## 5) Compatibility filters
- Every search mode must always apply the existing hard candidate filters:
  - existing Layer A `tour` only;
  - same `sales_mode` as the supplier offer;
  - not cancelled;
  - not completed;
  - future departure.
- Search results must remain admin/operator-only.
- Search must not expose customer/order/payment data.
- Service-layer validation remains authoritative before confirmation/mutation.

## 6) Result ordering
- Preserve stable compatible-list ordering unless date filtering narrows the set:
  - future departures first;
  - earlier departure first;
  - tour id ascending as tie-breaker.
- Title search should not introduce ranking/scoring in the first runtime slice.
- Date filter results should still be ordered by departure time, then id.
- Search context should be visible above results, for example:

```text
Search: title "Weekend" | page 1
```

or:

```text
Search: date 2026-09-01 | page 1
```

## 7) No-results behavior
- No title/date results means:
  - no mutation;
  - no selected target;
  - existing active link remains unchanged.
- Message should clearly say no compatible tours matched the title/date input.
- Controls should include:
  - back to compatible list;
  - search again;
  - manual `tour_id` / exact tour-code input;
  - back/home.
- No-results state must not clear the operator's ability to return to the base compatible list.

## 8) Fail-safe behavior
- No search path may create or modify tours.
- No search path may create, replace, or close execution links without explicit confirmation.
- Stale search results must be revalidated before confirmation/mutation.
- `sales_mode` mismatch remains blocked.
- Duplicate active-link create remains blocked.
- Replace with no active link remains blocked.
- Manual fallback remains available.
- Direct booking CTA remains controlled only by active authoritative link plus linked-tour bookability.
- Mini App, Layer A booking/payment, identity bridge, RFQ, and migration surfaces remain untouched.

## 9) Tests required
- Existing code search regressions:
  - exact code search still works;
  - partial code search still works;
  - same-`sales_mode` filter remains enforced;
  - selected code result opens confirmation.
- Title search:
  - title substring returns matching compatible tours;
  - wrong `sales_mode` title match is excluded;
  - cancelled/completed/past tours are excluded;
  - selected title result opens confirmation.
- Date hint/filter:
  - valid `YYYY-MM-DD` returns compatible tours on that date;
  - invalid date format returns clear admin-visible message and no mutation;
  - wrong `sales_mode` date match is excluded.
- No-results behavior:
  - no matching title/date returns no-results message;
  - manual fallback and back-to-compatible-list remain available.
- Callback/state safety:
  - query/date context is not stored in long callback payloads;
  - generated callback data remains `<= 64` UTF-8 bytes;
  - pagination preserves offer id, mode, query/date context, and page.
- Regression coverage:
  - compatible base list still works;
  - manual fallback still works;
  - create/replace/close/status flows still pass;
  - Mini App supplier-offer landing behavior remains unchanged.

## 10) First safe runtime slice recommendation
- Implement in two small runtime slices:
  1. title substring search only;
  2. date hint/filter only after title search is accepted.
- Keep Y33.2 code search behavior unchanged.
- Reuse the same candidate card, selection, confirmation, and service validation paths.
- Keep query/date context in FSM state when needed; do not place long input in callback data.
- Do not introduce fuzzy matching, ranking/scoring, or combined multi-field parsing in the first runtime slice.
- Do not add migrations.
- Do not touch Mini App, Layer A booking/payment, identity bridge, or API semantics.
