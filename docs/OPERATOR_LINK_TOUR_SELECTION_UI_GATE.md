# Operator Link Tour Selection UI Gate

## 1) Current state
- Telegram admin execution-link UI is available from `/admin_published` -> offer detail -> `Execution link`.
- Y32.7 accepted behavior:
  - admin can create an execution link with explicit existing `tour_id` or exact tour code;
  - admin can start replace flow when an active link exists;
  - confirmation screen shows offer/tour context and Mini App CTA warning;
  - status screen shows active link and link history;
  - close flow moves the offer to safe no-link state;
  - `sales_mode` mismatch is blocked with no state change.
- Current limitation:
  - operators must already know the target `tour_id` or exact tour code;
  - no compatible-tour browsing/search UI exists yet.
- This gate is docs-only. It does not change runtime code, migrations, Mini App, Layer A booking/payment, identity bridge, or API semantics.

## 2) Why manual ID/code is not enough
- Manual target entry is safe but operationally brittle:
  - operator must leave the flow or consult another surface to find a tour;
  - mistyped IDs/codes slow down moderation;
  - wrong-but-valid target risk remains if the operator copied the wrong value;
  - replacement decisions need side-by-side context, not only an identifier.
- A safe tour selection UI should improve discovery without weakening validation:
  - list only plausible candidates by default;
  - keep service-layer validation authoritative;
  - require explicit operator selection and confirmation;
  - never infer or auto-link by title/date/price similarity.

## 3) Required filters
- Hard filters for selectable candidates:
  - target is an existing Layer A `tour`;
  - target `sales_mode` matches the supplier offer `sales_mode`;
  - target status is visible to the operator;
  - target is not cancelled or completed;
  - target departure is in the future.
- Display requirements:
  - show status clearly even when allowed;
  - show seats available/total;
  - show actionability summary or warning when direct booking may remain unavailable;
  - show enough tour identity to avoid mistaken selection.
- Compatibility remains revalidated at confirmation/mutation time.
- Non-bookable but valid targets:
  - may be listed if backend validation permits;
  - must be marked as not necessarily self-service bookable;
  - must not cause Mini App direct CTA unless linked-tour policy says `bookable`.

## 4) Tour list card format
Each candidate card should include:

- `tour_id`
- tour code
- tour title
- tour status
- `sales_mode`
- departure datetime
- seats available/total
- customer actionability hint if available
- warning line when seats or policy mean Mini App CTA may stay disabled

Recommended concise Telegram card:

```text
Tour #3 (FULL-BUS-01)
Weekend Full Bus | status: open_for_sale | sales_mode: full_bus
Departure: 2026-09-01 08:00 | Seats: 0/40
CTA: not guaranteed; Mini App enables direct booking only if linked tour is bookable.
```

Selection button:

- `Select tour #3`

The card must not include customer PII, order lists, payment state, or supplier-private data beyond existing admin permissions.

## 5) Pagination rules
- Default page size should be small for Telegram readability:
  - recommended: 5 candidates per page;
  - maximum: 10 candidates per page.
- Ordering should be stable:
  - future departures first;
  - earlier departure first;
  - then tour id ascending;
  - optionally prioritize `open_for_sale` before other valid statuses.
- Pagination state must preserve:
  - offer id;
  - create vs replace mode;
  - search query/filter context;
  - current page.
- Controls:
  - `Prev`;
  - `Next`;
  - `Back to link status`;
  - `Manual tour_id/code input`.
- If candidates change between pages, selection must still revalidate the chosen tour before confirmation.

## 6) Search rules
- Search is optional after the first runtime slice, but allowed when bounded.
- Allowed search inputs:
  - exact or partial tour code;
  - title substring;
  - departure date (`YYYY-MM-DD`);
  - optional status filter if already supported by admin conventions.
- Search must always apply compatibility filters:
  - same `sales_mode`;
  - existing tour only;
  - not cancelled/completed;
  - future departure.
- Search must not:
  - auto-select the first result;
  - create a tour;
  - match by supplier-offer text heuristics without operator selection;
  - bypass confirmation;
  - broaden into booking/payment/order data.
- No result state should say:
  - no compatible tours found;
  - use manual ID/code if an operator has verified the target elsewhere;
  - create a Layer A tour separately if needed.

## 7) Create flow with tour selection
- Preconditions:
  - supplier offer is published;
  - no active execution link exists.
- Flow:
  1. Admin opens `/admin_published`.
  2. Admin opens offer detail.
  3. Admin taps `Execution link`.
  4. UI shows no active link.
  5. Admin taps `Create execution link`.
  6. UI shows compatible tour candidates.
  7. Admin selects one candidate or switches to manual ID/code input.
  8. UI shows confirmation with supplier offer summary and target tour summary.
  9. Admin confirms.
  10. Existing service/API creates the active link.
  11. UI refreshes status/history.
- If an active link appears before confirmation, create must stop and direct operator to replace.

## 8) Replace flow with tour selection
- Preconditions:
  - supplier offer is published;
  - active execution link exists.
- Flow:
  1. Admin opens execution link status.
  2. UI shows current active linked tour.
  3. Admin taps `Replace execution link`.
  4. UI shows compatible replacement candidates.
  5. Admin selects one candidate or switches to manual ID/code input.
  6. UI shows current active target and new target together.
  7. UI states the old link will close as `replaced`.
  8. Admin confirms.
  9. Existing service/API closes old active link and creates one new active link.
  10. UI refreshes status/history.
- Same-tour replacement should be treated as idempotent/no-op or rejected before mutation; it must not create duplicate history.

## 9) Fail-safe behavior
- No candidate selected means no mutation.
- Empty candidate list means no mutation.
- Search failure means no mutation.
- Pagination state loss means mutation controls are disabled until the operator restarts selection.
- Selected target must be revalidated before confirmation and again by service/API on mutation.
- If target becomes invalid between list and confirm, show a clear message and keep existing active link unchanged.
- If create detects an active link, stop and instruct operator to use replace.
- If replace detects no active link, stop and refresh status.
- If selected tour is non-bookable but valid, confirmation must warn that Mini App direct CTA may remain unavailable.
- Never create, clone, or modify tours from this flow.
- Never mutate Layer A booking, reservations, payments, RFQ state, or identity bridge.

## 10) Tests required
- Candidate list tests:
  - published offer with no active link shows `Create execution link` and compatible candidates;
  - published offer with active link shows `Replace execution link` and compatible candidates;
  - candidates are filtered by same `sales_mode`;
  - cancelled/completed/past tours are excluded or shown as non-selectable according to final runtime choice;
  - card shows id/code/title/status/`sales_mode`/seats/actionability warning.
- Pagination tests:
  - first page shows bounded number of candidates;
  - next/prev preserves offer id and create/replace mode;
  - selecting from page 2 still confirms the correct target.
- Search tests:
  - search by code/title/date narrows results;
  - no result state does not mutate links;
  - search results still respect compatibility filters.
- Mutation regression tests:
  - create via selected candidate creates one active link;
  - replace via selected candidate closes old link as `replaced`;
  - `sales_mode` mismatch remains blocked with admin-visible error and no state change;
  - existing manual ID/code path still works;
  - close/status/history from Y32.5/Y32.7 still works;
  - Mini App supplier-offer landing behavior remains unchanged.

## 11) First safe runtime slice recommendation
- Implement compatible candidate pagination before free-form search:
  1. add `Choose compatible tour` from create/replace target prompt;
  2. list future same-`sales_mode` non-cancelled/non-completed tours;
  3. show 5 candidates per page;
  4. allow `Select tour #{id}`;
  5. reuse existing confirmation screen and service/API mutation logic;
  6. keep manual ID/code input as fallback.
- Add bounded search only after the paginated compatible list is stable.
- Do not add migrations for this slice.
- Do not add Mini App logic.
- Do not add auto-tour creation.
- Keep all mutations behind existing create/replace confirmation and service-layer validation.
