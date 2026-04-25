# Operator Link Create/Replace UI Gate

## 1) Current accepted state
- Y32.5 accepted Telegram admin UI scope:
  - `/admin_published` -> offer detail -> `Execution link`;
  - admin can view execution link status;
  - admin can see active link details and recent history;
  - admin can close active link;
  - after close, no active link remains and direct booking CTA becomes unavailable through existing read-side resolver.
- Existing admin API/service primitives support:
  - create link;
  - replace link;
  - close link;
  - list link history.
- Mini App behavior remains read-side only:
  - direct booking CTA is controlled by active authoritative link plus linked-tour bookability;
  - no active link falls back to safe non-bookable state and catalog browsing.
- This gate is documentation-only. It does not change runtime code, migrations, Mini App, Layer A booking/payment, identity bridge, or API semantics.

## 2) Why create/replace was postponed
- Telegram admin UI had no safe tour-selection pattern yet.
- Free-form linking without a tour selection/confirmation flow risks:
  - wrong `tour_id`;
  - wrong `sales_mode`;
  - accidental replacement of a valid active link;
  - operators assuming a link creates bookability even when the linked tour is sold out or assisted-only.
- Create/replace requires more than a button:
  - candidate tour discovery;
  - compatibility filtering;
  - explicit confirmation;
  - clear warning that no tour/order/payment state is created or changed.
- Therefore Y32.5 intentionally shipped only view/history/close, which is reversible and fail-safe.

## 3) Required tour selection UX
- Entry point stays in Telegram admin published-offer detail:
  - `/admin_published` -> offer detail -> `Execution link`.
- Link status screen may show:
  - `Link to tour` when no active link exists;
  - `Replace link` when an active link exists.
- Tour selection must be explicit and bounded:
  - operator can enter an existing `tour_id` or tour code;
  - or operator can choose from a short candidate list returned by safe search;
  - UI must never offer `Create tour from this offer`.
- Candidate display must include:
  - tour id/code;
  - tour status;
  - `sales_mode`;
  - departure datetime;
  - seats available/total;
  - current customer-actionability hint if available.
- The operator must see the supplier offer summary and selected tour summary together before confirming.

## 4) Compatibility filters
- Required hard filters:
  - supplier offer exists;
  - supplier offer is published;
  - tour exists;
  - tour `sales_mode` matches supplier offer `sales_mode`;
  - tour status is safe to show/link by existing service validation;
  - tour departure is in the future;
  - create link requires no active link;
  - replace link must close previous active link and create exactly one new active link.
- Optional display filters for candidate lists:
  - default to future tours;
  - default to same `sales_mode`;
  - hide cancelled/completed tours;
  - show `open_for_sale` first.
- Non-bookable tour nuance:
  - operator may still link a non-bookable but otherwise valid tour if service validation allows it;
  - this does not enable direct booking CTA;
  - Mini App resolver remains authoritative and keeps CTA disabled for sold-out, assisted-only, view-only, or unavailable states.
- Invalid compatibility must fail closed with no link mutation.

## 5) Create link flow
- Preconditions:
  - supplier offer is published;
  - no active link exists.
- Flow:
  1. Admin opens `/admin_published`.
  2. Admin opens offer detail.
  3. Admin taps `Execution link`.
  4. UI shows no active link and offers `Link to tour`.
  5. Admin searches/selects existing compatible tour.
  6. UI shows confirmation screen.
  7. Admin confirms.
  8. Existing create-link admin API/service creates one active link.
  9. UI refreshes link status/history.
- If create is attempted while an active link exists, UI must stop and instruct operator to use replace.

## 6) Replace link flow
- Preconditions:
  - supplier offer is published;
  - active link exists;
  - replacement target is an existing compatible tour.
- Flow:
  1. Admin opens existing link status screen.
  2. Admin taps `Replace link`.
  3. UI shows current active linked tour.
  4. Admin searches/selects replacement tour.
  5. UI shows old target and new target together.
  6. UI states old link will close as `replaced`.
  7. Admin confirms.
  8. Existing replace-link admin API/service closes old link and creates one active new link.
  9. UI refreshes link status/history.
- Replacing with the same active target should be idempotent or rejected as no-op; it must not create duplicate history rows.

## 7) Confirmation / danger messages
- Create confirmation:
  - `This links supplier offer #{offer_id} to existing tour #{tour_id}. No tour, order, reservation, payment, or RFQ state will be created.`
- Replace confirmation:
  - `This closes the current active link as replaced and activates tour #{tour_id}. Customer CTA may remain unavailable if the new tour is not bookable.`
- Sales-mode mismatch:
  - `Cannot link: supplier offer sales_mode and tour sales_mode differ.`
- Non-bookable linked tour warning:
  - `This tour may be visible as a link but is not currently bookable. Mini App will keep direct booking CTA disabled.`
- Auto-create prohibition:
  - `No matching tour was found. Create a Layer A tour separately; this UI never creates tours from supplier offers.`
- Final confirmation button should use explicit language:
  - `Confirm link`;
  - `Confirm replace`;
  - never ambiguous labels like `OK`.

## 8) Fail-safe behavior
- If no tour is selected, do not call create/replace.
- If selected tour fails compatibility, do not call create/replace.
- If backend/API validation fails, keep existing active link unchanged.
- If create detects existing active link, show `Use Replace link instead`.
- If replace fails after validation, keep showing the pre-existing link state after refresh.
- If linked tour later becomes non-bookable, do not mutate link automatically; Mini App resolver disables direct CTA.
- If the UI cannot refresh current state, disable mutation buttons and ask operator to retry.
- Never infer link targets from title/date/price/text matching without explicit operator confirmation.

## 9) Tests required
- Unit/callback tests:
  - published offer with no active link shows `Link to tour`;
  - published offer with active link shows `Replace link`;
  - candidate tour with matching `sales_mode` can reach confirmation;
  - candidate tour with mismatched `sales_mode` shows validation message and does not call service;
  - create confirmation calls create-link service/API once;
  - replace confirmation calls replace-link service/API once and old link becomes closed;
  - no duplicate active link remains after create/replace;
  - non-bookable linked tour warning is displayed but does not bypass resolver.
- Regression tests:
  - Y32.5 view/history/close still works;
  - Mini App supplier-offer landing behavior remains unchanged;
  - Layer A booking/payment tests are not affected.

## 10) First safe runtime slice recommendation
- Implement create/replace in two small slices:
  1. `tour_id` / tour-code input + compatibility preview + confirmation;
  2. optional candidate-list search/pagination if operators need discovery.
- Start with explicit `tour_id` or exact tour code, because it is less ambiguous than text search.
- Reuse existing admin API/service primitives:
  - create: `POST /admin/supplier-offers/{id}/link-tour`;
  - replace: `POST /admin/supplier-offers/{id}/replace-link`;
  - history: `GET /admin/supplier-offers/{id}/links`.
- Do not add migrations for this UI slice.
- Do not add Mini App logic.
- Do not add auto-tour creation.
- Keep create/replace Telegram UI admin-only and fail-closed.
